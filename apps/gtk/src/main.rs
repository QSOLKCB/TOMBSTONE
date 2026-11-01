//! Optional GTK4 desktop frontend. All evidence semantics are in C99 via
//! tombstone-ffi; workflow orchestration is shared with the Phase 5 TUI.
//! Only GTK's C ABI is used, with NO external Rust crates.
use std::env;
use std::ffi::{c_char, c_int, c_void, CStr, CString};
use std::ptr;
use std::process;
use tombstone_ffi as engine;
use tombstone_tui as work;

const HELP: &str = "TOMBSTONE GTK4 — optional desktop frontend\n\
Usage: tombstone-gtk [--help|--smoke-test]\n\
Requires GTK4 and a desktop display. --smoke-test runs a GTK startup/C99\n\
integration check under a display server (CI uses Xvfb).\n\
The application never deletes input files; receipt saving is explicit\n\
and create-new only. C99 owns all evidence and hash calculations.\n";

const HASH_ABC: &str =
    "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";

// All pointers below are GTK-owned widgets valid for the duration of
// g_application_run. AppState is Box-owned by main; callbacks run only
// on the single GTK main loop and never retain Rust slices beyond a call.
struct AppState {
    fingerprint: *mut c_void,
    observe_before: *mut c_void,
    observe_after: *mut c_void,
    observe_prev: *mut c_void,
    delete_before: *mut c_void,
    delete_removed: *mut c_void,
    delete_after: *mut c_void,
    delete_offset: *mut c_void,
    delete_prev: *mut c_void,
    inspect: *mut c_void,
    chain: *mut c_void,
    trusted: *mut c_void,
    save_path: *mut c_void,
    output: *mut c_void,
    last_receipt: Option<String>,
    smoke: bool,
    smoke_ok: bool,
    smoke_reused: bool,
    app: *mut c_void,
}
impl AppState {
    fn new(smoke: bool) -> Self {
        Self {
            fingerprint: ptr::null_mut(),
            observe_before: ptr::null_mut(), observe_after: ptr::null_mut(),
            observe_prev: ptr::null_mut(), delete_before: ptr::null_mut(),
            delete_removed: ptr::null_mut(), delete_after: ptr::null_mut(),
            delete_offset: ptr::null_mut(), delete_prev: ptr::null_mut(),
            inspect: ptr::null_mut(), chain: ptr::null_mut(),
            trusted: ptr::null_mut(), save_path: ptr::null_mut(),
            output: ptr::null_mut(), last_receipt: None, smoke, smoke_ok: false,
            smoke_reused: false, app: ptr::null_mut(),
        }
    }

    fn display(&mut self, message: &str) {
        // SAFETY: called on GTK's main thread; output is a live GtkTextView.
        // GTK copies the string contents synchronously.
        if self.output.is_null() { return; }
        let safe = CString::new(message)
            .unwrap_or_else(|_| CString::new("Invalid display text").expect("constant"));
        unsafe {
            let buffer = gtk_text_view_get_buffer(self.output);
            gtk_text_buffer_set_text(buffer, safe.as_ptr(), -1);
        }
    }

    fn result(&mut self, result: Result<work::Report, String>) {
        self.last_receipt = None; // prevent exporting a prior/stale receipt
        match result {
            Ok(report) => {
                let mut lines = vec![report.title];
                lines.extend(report.lines);
                self.last_receipt = report.export_json;
                self.display(&lines.join("\n"));
            }
            Err(error) => self.display(&format!(
                "Unable to complete operation.\n{}\n\nNo evidence was exported.", error
            )),
        }
    }

    fn field(&self, widget: *mut c_void) -> Result<String, String> {
        if widget.is_null() { return Err("UI input unavailable.".into()); }
        // SAFETY: GtkEditable pointer is live; returned NUL-terminated
        // string remains GTK-owned and is immediately copied into Rust.
        let raw = unsafe { gtk_editable_get_text(widget) };
        if raw.is_null() { return Err("UI input unavailable.".into()); }
        unsafe { CStr::from_ptr(raw) }.to_str()
            .map(str::to_owned)
            .map_err(|_| "Input must be valid UTF-8.".into())
    }

    fn run_hash(&self) -> Result<work::Report, String> {
        work::fingerprint(&self.field(self.fingerprint)?)
    }
    fn run_observe(&self) -> Result<work::Report, String> {
        let prev = self.field(self.observe_prev)?;
        work::observe(
            &self.field(self.observe_before)?,
            &self.field(self.observe_after)?,
            if prev.is_empty() { None } else { Some(&prev) },
        )
    }
    fn run_delete(&self) -> Result<work::Report, String> {
        let prev = self.field(self.delete_prev)?;
        work::witness(
            &self.field(self.delete_before)?,
            &self.field(self.delete_removed)?,
            &self.field(self.delete_after)?,
            &self.field(self.delete_offset)?,
            if prev.is_empty() { None } else { Some(&prev) },
        )
    }
    fn run_inspect(&self) -> Result<work::Report, String> {
        work::inspect(&self.field(self.inspect)?)
    }
    fn run_chain(&self) -> Result<work::Report, String> {
        let entered = self.field(self.chain)?;
        // One line-like UTF-8 entry separated by |. Exact user-provided
        // ordering is retained: C99 checks the links, not filename sorting.
        let paths: Vec<String> = entered.split('|').map(|s| s.trim().to_owned()).collect();
        if paths.iter().any(|p| p.is_empty()) {
            return Err("Enter receipt files separated by |, in genesis-to-head order.".into());
        }
        let head = self.field(self.trusted)?;
        work::chain(&paths, if head.is_empty() { None } else { Some(&head) })
    }

    fn run_save(&self) -> Result<String, String> {
        let canonical = self.last_receipt.as_ref()
            .ok_or_else(|| "No generated/inspected canonical receipt to save.".to_owned())?;
        let target = self.field(self.save_path)?;
        work::export_receipt(canonical, &target)?;
        Ok("Canonical receipt saved to a new file. Existing files were not overwritten.".into())
    }
}

// GTK4 and GLib/GIO/GObject C ABIs. These bindings cover only UI widgets,
// signal connection and the synchronous main loop. The C99 evidence ABI is
// entirely handled by tombstone-ffi.
#[link(name = "gtk-4")]
extern "C" {
    fn gtk_application_new(id: *const c_char, flags: c_int) -> *mut c_void;
    fn gtk_application_window_new(app: *mut c_void) -> *mut c_void;
    fn gtk_application_get_windows(app: *mut c_void) -> *mut c_void;
    fn gtk_window_set_title(window: *mut c_void, text: *const c_char);
    fn gtk_window_set_default_size(window: *mut c_void, width: c_int, height: c_int);
    fn gtk_window_set_child(window: *mut c_void, child: *mut c_void);
    fn gtk_window_present(window: *mut c_void);
    fn gtk_box_new(orientation: c_int, spacing: c_int) -> *mut c_void;
    fn gtk_box_append(container: *mut c_void, child: *mut c_void);
    fn gtk_notebook_new() -> *mut c_void;
    fn gtk_notebook_append_page(book: *mut c_void, child: *mut c_void, tab: *mut c_void) -> c_int;
    fn gtk_label_new(text: *const c_char) -> *mut c_void;
    fn gtk_label_set_xalign(label: *mut c_void, x: f32);
    fn gtk_label_set_wrap(label: *mut c_void, wrap: c_int);
    fn gtk_entry_new() -> *mut c_void;
    fn gtk_entry_set_placeholder_text(entry: *mut c_void, text: *const c_char);
    fn gtk_editable_get_text(editable: *mut c_void) -> *const c_char;
    fn gtk_button_new_with_label(text: *const c_char) -> *mut c_void;
    fn gtk_scrolled_window_new() -> *mut c_void;
    fn gtk_scrolled_window_set_child(scroll: *mut c_void, child: *mut c_void);
    fn gtk_text_view_new() -> *mut c_void;
    fn gtk_text_view_set_editable(view: *mut c_void, editable: c_int);
    fn gtk_text_view_set_cursor_visible(view: *mut c_void, visible: c_int);
    fn gtk_text_view_set_monospace(view: *mut c_void, enabled: c_int);
    fn gtk_text_view_set_wrap_mode(view: *mut c_void, mode: c_int);
    fn gtk_text_view_get_buffer(view: *mut c_void) -> *mut c_void;
    fn gtk_text_buffer_set_text(buffer: *mut c_void, text: *const c_char, length: c_int);
    fn gtk_widget_set_vexpand(widget: *mut c_void, expand: c_int);
    fn gtk_widget_set_hexpand(widget: *mut c_void, expand: c_int);
    fn gtk_widget_set_margin_top(widget: *mut c_void, margin: c_int);
    fn gtk_widget_set_margin_bottom(widget: *mut c_void, margin: c_int);
    fn gtk_widget_set_margin_start(widget: *mut c_void, margin: c_int);
    fn gtk_widget_set_margin_end(widget: *mut c_void, margin: c_int);
}
#[link(name = "gobject-2.0")]
extern "C" {
    fn g_signal_connect_data(
        instance: *mut c_void,
        signal: *const c_char,
        callback: unsafe extern "C" fn(*mut c_void, *mut c_void),
        data: *mut c_void,
        destroy: Option<unsafe extern "C" fn(*mut c_void, *mut c_void)>,
        flags: c_int,
    ) -> u64;
    fn g_object_unref(object: *mut c_void);
}
#[link(name = "gio-2.0")]
extern "C" {
    fn g_application_run(app: *mut c_void, argc: c_int, argv: *mut *mut c_char) -> c_int;
    fn g_application_quit(app: *mut c_void);
    fn g_application_activate(app: *mut c_void);
}

// GTK returns a borrowed GList; use GLib's public accessor rather than
// depending on the native GList memory layout.
#[link(name = "glib-2.0")]
extern "C" {
    fn g_list_nth_data(list: *mut c_void, n: u32) -> *mut c_void;
    fn g_idle_add(callback: unsafe extern "C" fn(*mut c_void) -> c_int,
                  data: *mut c_void) -> u32;
}

fn c(text: &str) -> CString {
    // Only static labels and constant protocol strings should reach here.
    CString::new(text).expect("static GTK label must not contain NUL")
}
unsafe fn text_label(parent: *mut c_void, content: &str) {
    let label = gtk_label_new(c(content).as_ptr());
    gtk_label_set_xalign(label, 0.0);
    gtk_label_set_wrap(label, 1);
    gtk_box_append(parent, label);
}
unsafe fn entry(parent: *mut c_void, label: &str, hint: &str) -> *mut c_void {
    text_label(parent, label);
    let widget = gtk_entry_new();
    gtk_entry_set_placeholder_text(widget, c(hint).as_ptr());
    gtk_widget_set_hexpand(widget, 1);
    gtk_box_append(parent, widget);
    widget
}
unsafe fn button(
    parent: *mut c_void, text: &str,
    callback: unsafe extern "C" fn(*mut c_void, *mut c_void),
    state: *mut c_void,
) {
    let widget = gtk_button_new_with_label(c(text).as_ptr());
    gtk_box_append(parent, widget);
    g_signal_connect_data(widget, c("clicked").as_ptr(), callback, state, None, 0);
}
unsafe fn tab(book: *mut c_void, title: &str) -> *mut c_void {
    let page = gtk_box_new(1, 8);
    for set in [
        gtk_widget_set_margin_top as unsafe extern "C" fn(*mut c_void, c_int),
        gtk_widget_set_margin_bottom,
        gtk_widget_set_margin_start,
        gtk_widget_set_margin_end,
    ] { set(page, 12); }
    gtk_notebook_append_page(book, page, gtk_label_new(c(title).as_ptr()));
    page
}

unsafe extern "C" fn clicked_hash(_: *mut c_void, data: *mut c_void) {
    let state = &mut *(data as *mut AppState);
    let result = state.run_hash();
    state.result(result);
}
unsafe extern "C" fn clicked_observe(_: *mut c_void, data: *mut c_void) {
    let state = &mut *(data as *mut AppState);
    let result = state.run_observe();
    state.result(result);
}
unsafe extern "C" fn clicked_witness(_: *mut c_void, data: *mut c_void) {
    let state = &mut *(data as *mut AppState);
    let result = state.run_delete();
    state.result(result);
}
unsafe extern "C" fn clicked_inspect(_: *mut c_void, data: *mut c_void) {
    let state = &mut *(data as *mut AppState);
    let result = state.run_inspect();
    state.result(result);
}
unsafe extern "C" fn clicked_chain(_: *mut c_void, data: *mut c_void) {
    let state = &mut *(data as *mut AppState);
    let result = state.run_chain();
    state.result(result);
}
unsafe extern "C" fn clicked_save(_: *mut c_void, data: *mut c_void) {
    let state = &mut *(data as *mut AppState);
    let outcome = state.run_save();
    match outcome {
        Ok(text) => state.display(&text),
        Err(error) => state.display(&format!("Receipt was NOT saved.\n{error}")),
    }
}

// On a second launch, GtkApplication routes activation to the existing process.
// Reuse its live window; otherwise the shared AppState would be repointed to
// widgets owned by the new window, potentially leaving dangling pointers.
unsafe extern "C" fn activate(app: *mut c_void, data: *mut c_void) {
    let state = &mut *(data as *mut AppState);
    let existing = g_list_nth_data(gtk_application_get_windows(app), 0);
    if !existing.is_null() {
        if state.smoke { state.smoke_reused = true; }
        gtk_window_present(existing);
        return;
    }
    // Any previous window has been destroyed; no old widgets are active.
    state.last_receipt = None;
    let window = gtk_application_window_new(app);
    gtk_window_set_title(window, c("TOMBSTONE — cryptographic evidence").as_ptr());
    gtk_window_set_default_size(window, 1000, 720);

    let vertical = gtk_box_new(1, 10);
    gtk_widget_set_margin_top(vertical, 12);
    gtk_widget_set_margin_bottom(vertical, 12);
    gtk_widget_set_margin_start(vertical, 16);
    gtk_widget_set_margin_end(vertical, 16);
    gtk_window_set_child(window, vertical);

    text_label(vertical, "TOMBSTONE  /  THE DATA IS GONE. THE TOMBSTONE HAS A CHECKSUM.");
    text_label(vertical, "C99 evidence engine | no automatic file deletion | offline | v1 receipt profile");
    let notebook = gtk_notebook_new();
    gtk_box_append(vertical, notebook);

    let page = tab(notebook, "Fingerprint");
    state.fingerprint = entry(page, "File to fingerprint", "Full path to file (UTF-8)");
    button(page, "SHA-256 fingerprint", clicked_hash, data);

    let page = tab(notebook, "Observe");
    state.observe_before = entry(page, "Before file", "Existing before-file path");
    state.observe_after = entry(page, "After file", "Existing after-file path");
    state.observe_prev = entry(page, "Previous receipt SHA-256 (optional)", "Leave blank for genesis");
    button(page, "Record observed transition", clicked_observe, data);

    let page = tab(notebook, "Witness deletion");
    state.delete_before = entry(page, "Before file", "Exact original bytes");
    state.delete_removed = entry(page, "Removed span file", "Exact removed bytes (not deleted by TOMBSTONE)");
    state.delete_after = entry(page, "After file", "Resulting bytes");
    state.delete_offset = entry(page, "Removed span byte offset", "0-based decimal index");
    state.delete_prev = entry(page, "Previous receipt SHA-256 (optional)", "Leave blank for genesis");
    button(page, "Verify supplied splice", clicked_witness, data);

    let page = tab(notebook, "Inspect receipt");
    state.inspect = entry(page, "Canonical receipt file", "JSON receipt path");
    button(page, "Verify receipt self-hash", clicked_inspect, data);
    text_label(page, "Self-hash verification is not proof of an authenticated history.");

    let page = tab(notebook, "Verify chain");
    state.chain = entry(page, "Receipt paths, in genesis-to-head order", "first.json|second.json|third.json");
    state.trusted = entry(page, "Independently trusted final receipt SHA-256 (optional)", "Leave blank for local-only validation");
    button(page, "Verify full ordered chain", clicked_chain, data);
    text_label(page, "An unanchored locally consistent chain can be rewritten wholesale.");

    let page = tab(notebook, "Save receipt");
    state.save_path = entry(page, "New receipt destination", "Destination must NOT already exist");
    button(page, "Save last canonical receipt to NEW file", clicked_save, data);
    text_label(page, "No files are automatically written; saved receipts contain no plaintext or paths.");

    text_label(vertical, "C99 result / receipt (read-only; never edits input files)");
    let scroller = gtk_scrolled_window_new();
    gtk_widget_set_vexpand(scroller, 1);
    gtk_widget_set_hexpand(scroller, 1);
    state.output = gtk_text_view_new();
    gtk_text_view_set_editable(state.output, 0);
    gtk_text_view_set_cursor_visible(state.output, 0);
    gtk_text_view_set_monospace(state.output, 1);
    gtk_text_view_set_wrap_mode(state.output, 2); // GTK_WRAP_WORD
    gtk_scrolled_window_set_child(scroller, state.output);
    gtk_box_append(vertical, scroller);
    state.display("Choose a tab and supply local file paths.\nNo inputs are deleted.\n\
A verified splice proves only a mathematical relationship among supplied byte buffers.");

    gtk_window_present(window);

    if state.smoke {
        state.smoke_ok = engine::sha256(b"abc")
            .and_then(|digest| engine::to_hex(&digest))
            .map(|digest| digest == HASH_ABC)
            .unwrap_or(false);
        // Schedule a second activation AFTER this callback returns. That
        // exercises the real GTK activation route without re-entrant &mut
        // references to AppState. The callback verifies one window remains.
        state.app = app;
        if g_idle_add(smoke_repeat_activation, data) == 0 {
            state.smoke_ok = false;
            g_application_quit(app);
        }
    }
}

// Called on the GTK main loop after the initial activate callback returns.
unsafe extern "C" fn smoke_repeat_activation(data: *mut c_void) -> c_int {
    // Read the raw pointer BEFORE reactivating, with no Rust reference held
    // across g_application_activate's synchronous nested callback.
    let app = (*(data as *mut AppState)).app;
    g_application_activate(app);
    let state = &mut *(data as *mut AppState);
    let windows = gtk_application_get_windows(app);
    let first = g_list_nth_data(windows, 0);
    let second = g_list_nth_data(windows, 1);
    state.smoke_ok = state.smoke_ok && state.smoke_reused
        && !first.is_null() && second.is_null();
    g_application_quit(app);
    0 // remove the idle callback
}

fn main() {
    // Do not use env::args(), which can leak non-UTF-8 paths in panic output.
    let args = match env::args_os().skip(1)
        .map(|item| item.into_string()).collect::<Result<Vec<_>, _>>() {
        Ok(args) => args,
        Err(_) => {
            eprintln!("tombstone-gtk: arguments must be valid UTF-8");
            process::exit(2);
        }
    };
    if args.len() == 1 && args[0] == "--help" { print!("{HELP}"); return; }
    let smoke = args.len() == 1 && args[0] == "--smoke-test";
    if !args.is_empty() && !smoke {
        eprintln!("tombstone-gtk: only --help is accepted for regular use");
        process::exit(2);
    }
    if engine::check_abi().is_err() {
        eprintln!("tombstone-gtk: native C99 ABI mismatch");
        process::exit(3);
    }

    // SAFETY: one thread owns GTK's application main loop, AppState pointers
    // survive throughout callbacks, then the GTK app is unref'd before drop.
    unsafe {
        let app = gtk_application_new(c("org.qsolkcb.Tombstone").as_ptr(), 0);
        if app.is_null() {
            eprintln!("tombstone-gtk: could not initialize desktop application");
            process::exit(2);
        }
        let mut state = Box::new(AppState::new(smoke));
        let user_data = (&mut *state) as *mut AppState as *mut c_void;
        g_signal_connect_data(app, c("activate").as_ptr(), activate, user_data, None, 0);
        let code = g_application_run(app, 0, ptr::null_mut());
        g_object_unref(app);
        if smoke {
            if code == 0 && state.smoke_ok {
                println!("PASS: GTK4 activated, repeat activation reused one window, and C99 SHA-256 checked");
                return;
            }
            eprintln!("tombstone-gtk: GTK/C99 desktop smoke check failed");
            process::exit(3);
        }
        process::exit(code);
    }
}
