//! Interactive ncurses screen, navigation and prompts only.
//! All receipt and evidence decisions are in the C99 engine via tombstone-ffi.
use std::env;
use std::ffi::CString;
use std::io::{self, IsTerminal};
use std::os::raw::{c_char, c_int, c_void};
use std::process;
use tombstone_tui::{self as work, Report};

#[link(name = "ncursesw")]
extern "C" {
    fn initscr() -> *mut c_void;
    fn endwin() -> c_int;
    fn raw() -> c_int;
    fn noecho() -> c_int;
    fn echo() -> c_int;
    fn keypad(win: *mut c_void, enabled: c_int) -> c_int;
    fn curs_set(visibility: c_int) -> c_int;
    fn erase() -> c_int;
    fn refresh() -> c_int;
    fn mvaddnstr(row: c_int, col: c_int, text: *const c_char, length: c_int) -> c_int;
    fn getch() -> c_int;
    fn getnstr(buffer: *mut c_char, length: c_int) -> c_int;
    static mut stdscr: *mut c_void;
    static mut LINES: c_int;
    static mut COLS: c_int;
}

const HELP: &str = "TOMBSTONE TUI (Phase 5)\n\
Usage: tombstone-tui\n\
Requires an interactive UTF-8 terminal and system ncursesw.\n\
Keys: j/k or arrows to select, Enter to run, 1-5 quick select, q to quit.\n\
Receipt viewer: j/k scroll; s saves ONLY a generated canonical receipt\n\
to a NEW file (never overwrites); b/Enter returns, q exits.\n\
Workflows: hash file, observe transition, witness supplied deletion,\n\
inspect receipt self-hash, verify complete ordered chain.\n\
C99 owns all cryptographic evidence; TUI never deletes input files.\n";

const MENU: [&str; 5] = [
    "1  SHA-256 fingerprint a file",
    "2  Observe a before/after transition",
    "3  Witness a caller-supplied deletion splice",
    "4  Inspect one canonical receipt / self-hash",
    "5  Verify a complete ordered receipt chain",
];

struct Terminal;
impl Terminal {
    fn start() -> Result<Self, &'static str> {
        // SAFETY: check a real tty before ncurses initialisation; all calls
        // are owned by this single-threaded TUI and reversed by Drop.
        unsafe {
            if initscr().is_null() { return Err("could not initialise terminal UI"); }
            if raw() == -1 || noecho() == -1 || keypad(stdscr, 1) == -1 {
                endwin();
                return Err("could not configure terminal UI");
            }
            curs_set(0);
        }
        Ok(Self)
    }

    fn size(&self) -> (usize, usize) {
        // SAFETY: ncurses exports these dimensions once initscr succeeds.
        unsafe { (COLS.max(0) as usize, LINES.max(0) as usize) }
    }

    fn line(&self, y: usize, text: &str) {
        let (width, height) = self.size();
        if y >= height || width < 2 { return; }
        // Display only printable ASCII. This prevents control/escape
        // sequences in input or receipts from manipulating the terminal.
        let clean: String = text.chars().map(|c| {
            if c.is_ascii_graphic() || c == ' ' { c } else { '?' }
        }).take(width.saturating_sub(2)).collect();
        if let Ok(cstr) = CString::new(clean) {
            // SAFETY: cstr lives through the synchronous ncurses call.
            unsafe { mvaddnstr(y as c_int, 1, cstr.as_ptr(), (width - 2) as c_int); }
        }
    }

    fn redraw(&self) {
        // SAFETY: ncurses screen is initialised and exclusively owned here.
        unsafe { erase(); }
    }
    fn flush(&self) { unsafe { refresh(); } }
    fn key(&self) -> c_int { unsafe { getch() } }

    fn prompt(&self, question: &str) -> Result<String, String> {
        let (width, height) = self.size();
        if width < 50 || height < 12 {
            return Err("Resize terminal to at least 50 columns and 12 rows.".into());
        }
        unsafe { erase(); }
        self.line(0, "TOMBSTONE | private input (not logged)");
        self.line(2, question);
        self.line(4, "Enter text and press Return. Use ~ to cancel.");
        self.line(6, "> ");
        self.flush();
        let mut input = [0 as c_char; 241];
        // SAFETY: getnstr writes <= 240 bytes plus NUL, bounded by the
        // buffer. Echo is enabled only for this prompt; screen is then cleared.
        let status = unsafe {
            curs_set(1);
            echo();
            let status = getnstr(input.as_mut_ptr(), 240);
            noecho();
            curs_set(0);
            erase();
            status
        };
        if status == -1 { return Err("Terminal input failed.".into()); }
        let len = input.iter().position(|c| *c == 0)
            .unwrap_or(input.len());
        let bytes: Vec<u8> = input[..len].iter().map(|c| *c as u8).collect();
        let value = String::from_utf8(bytes)
            .map_err(|_| "Input must use valid UTF-8.".to_owned())?;
        if value == "~" { return Err("Cancelled; no files changed.".into()); }
        Ok(value)
    }
}
impl Drop for Terminal {
    fn drop(&mut self) {
        // SAFETY: this is the single owner of the ncurses session.
        unsafe { endwin(); }
    }
}

fn wrap_text(lines: &[String], width: usize) -> Vec<String> {
    let limit = width.saturating_sub(3).max(1);
    let mut output = Vec::new();
    for line in lines {
        let chars: Vec<char> = line.chars().collect();
        if chars.is_empty() { output.push(String::new()); continue; }
        for group in chars.chunks(limit) { output.push(group.iter().collect()); }
    }
    output
}

fn menu(term: &Terminal, chosen: usize, message: &str) {
    term.redraw();
    let (width, height) = term.size();
    if width < 50 || height < 12 {
        term.line(0, "Resize to >= 50 columns x 12 rows");
    } else {
        term.line(0, "TOMBSTONE  /  cryptographic deletion evidence  /  C99");
        term.line(2, "Choose workflow (j/k, arrows, Enter or 1-5):");
        for (index, option) in MENU.iter().enumerate() {
            term.line(index + 4, &format!("{} {}", if chosen == index { ">" } else { " " }, option));
        }
        term.line(10, "q: quit   h: help   Nothing here modifies or deletes input files.");
        if !message.is_empty() { term.line(height - 2, message); }
    }
    term.flush();
}

fn workflow(term: &Terminal, selected: usize) -> Result<Report, String> {
    match selected {
        0 => {
            let path = term.prompt("File to fingerprint (UTF-8 path):")?;
            work::fingerprint(&path)
        }
        1 => {
            let before = term.prompt("Before-file path:")?;
            let after = term.prompt("After-file path:")?;
            let prior = term.prompt("Previous receipt SHA-256 (blank for genesis):")?;
            work::observe(&before, &after,
                          if prior.is_empty() { None } else { Some(&prior) })
        }
        2 => {
            let before = term.prompt("Before-file path:")?;
            let removed = term.prompt("Removed-bytes file path:")?;
            let after = term.prompt("After-file path:")?;
            let offset = term.prompt("Byte offset for removed span (decimal):")?;
            let prior = term.prompt("Previous receipt SHA-256 (blank for genesis):")?;
            work::witness(&before, &removed, &after, &offset,
                          if prior.is_empty() { None } else { Some(&prior) })
        }
        3 => {
            let path = term.prompt("Receipt JSON file path:")?;
            work::inspect(&path)
        }
        4 => {
            let count = term.prompt("How many ordered receipts? (1 to 64):")?;
            let n: usize = count.parse().map_err(|_| "Invalid receipt count.".to_owned())?;
            if n == 0 || n > work::MAX_CHAIN {
                return Err("Receipt count must be between 1 and 64.".into());
            }
            let mut paths = Vec::with_capacity(n);
            for i in 0..n {
                paths.push(term.prompt(&format!("Receipt {} of {} (genesis first):", i + 1, n))?);
            }
            let head = term.prompt("External trusted final hash (blank for local-only check):")?;
            work::chain(&paths, if head.is_empty() { None } else { Some(&head) })
        }
        _ => Err("Invalid action.".into()),
    }
}

fn result_screen(term: &Terminal, report: Report) -> bool {
    let mut scroll = 0usize;
    let mut note = String::new();
    loop {
        let (width, height) = term.size();
        let display = wrap_text(&report.lines, width);
        let visible = height.saturating_sub(6);
        let max_scroll = display.len().saturating_sub(visible);
        scroll = scroll.min(max_scroll);
        term.redraw();
        term.line(0, &format!("TOMBSTONE | {}", report.title));
        term.line(1, "Evidence produced/verified only by C99.");
        for (row, text) in display.iter().skip(scroll).take(visible).enumerate() {
            term.line(row + 3, text);
        }
        if height >= 4 {
            term.line(height - 3, &format!("Scroll {}/{} (j/k, arrows).  b/Enter back, q quit{}",
                scroll, max_scroll,
                if report.export_json.is_some() { ", s save receipt" } else { "" }));
            if !note.is_empty() { term.line(height - 2, &note); }
        }
        term.flush();
        match term.key() {
            113 | 3 => return true, // q / Ctrl-C
            98 | 10 | 13 | 27 => return false, // b, Return, Escape
            106 | 258 => scroll = (scroll + 1).min(max_scroll), // j/down
            107 | 259 => scroll = scroll.saturating_sub(1), // k/up
            115 => if let Some(json) = &report.export_json {
                let path = term.prompt("Save canonical receipt to NEW file (no overwrite):");
                note = match path {
                    Ok(path) => match work::export_receipt(json, &path) {
                        Ok(()) => "Receipt saved. Existing files were not overwritten.".into(),
                        Err(error) => error,
                    },
                    Err(error) => error,
                };
            },
            _ => (),
        }
    }
}

fn run() -> Result<(), &'static str> {
    if !io::stdin().is_terminal() || !io::stdout().is_terminal() {
        return Err("an interactive terminal is required (use the headless tombstone CLI for automation)");
    }
    if env::var("TERM").ok().as_deref().map_or(true, |value| value == "dumb" || value.is_empty()) {
        return Err("an interactive terminal with TERM configured is required");
    }
    tombstone_ffi::check_abi().map_err(|_| "C99 ABI version mismatch")?;
    let terminal = Terminal::start()?;
    let mut selected = 0usize;
    let mut message = String::new();
    loop {
        menu(&terminal, selected, &message);
        let key = terminal.key();
        match key {
            113 | 3 => return Ok(()), // quit
            104 => { // help
                let report = Report { title: "Help".into(), lines: HELP.lines().map(str::to_owned).collect(), export_json: None };
                if result_screen(&terminal, report) { return Ok(()); }
            }
            106 | 258 => selected = (selected + 1) % MENU.len(),
            107 | 259 => selected = (selected + MENU.len() - 1) % MENU.len(),
            49..=53 => selected = (key - 49) as usize,
            10 | 13 | 343 => {
                match workflow(&terminal, selected) {
                    Ok(result) => {
                        message.clear();
                        if result_screen(&terminal, result) { return Ok(()); }
                    }
                    Err(error) => message = error,
                }
            }
            _ => (),
        }
    }
}

fn main() {
    // Never use env::args(); a malformed Unix filename could panic with
    // the argument bytes in stderr, violating our privacy contract.
    let args: Vec<String> = match env::args_os().skip(1)
        .map(|v| v.into_string()).collect::<Result<Vec<_>, _>>() {
        Ok(values) => values,
        Err(_) => {
            eprintln!("tombstone-tui: arguments must be valid UTF-8");
            process::exit(2);
        }
    };
    if args.len() == 1 && args[0] == "--help" { print!("{HELP}"); return; }
    if !args.is_empty() {
        eprintln!("tombstone-tui: only --help is accepted");
        process::exit(2);
    }
    if let Err(error) = run() {
        eprintln!("tombstone-tui: {error}");
        process::exit(2);
    }
}
