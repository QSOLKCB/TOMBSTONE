//! Noninteractive, deterministic interface to the authoritative C99 engine.
//! File names are inputs only; neither emitted receipts nor diagnostics log them.
use std::env;
use std::fs::File;
use std::io::{self, Read, Write};
use std::process;
use tombstone_ffi as core;

const MAX_INPUT: u64 = 64 * 1024 * 1024;
const HELP: &str = "\
TOMBSTONE — Phase 4 C99-backed CLI

Usage:
  tombstone hash <file|->
  tombstone observe <before> <after> [--previous <64-lowercase-hex>]
  tombstone delete <before> <removed> <after> <byte-offset> [--previous <64-lowercase-hex>]
  tombstone verify <receipt|->
  tombstone verify-chain <receipt>... [--trusted-head <64-lowercase-hex>|--trusted-head-file <path>]
  tombstone --help

All evidence commands emit one JSON object and a newline to stdout.
Errors go to stderr with a nonzero status (2=usage, 3=invalid evidence,
4=I/O). '-' reads standard input; supply it at most once per command.
Receipts contain no plaintext, file paths or timestamps. This tool never
deletes files and does not prove historical edits or secure erasure.
verify checks ONE receipt's self-hash; verify-chain checks a full genesis
chain, optionally against an independently trusted final hash.
--trusted-head-file reads a strict, externally retained 64-hex head (optional LF).
A matching digest is not proof of a historical deletion, identity or time.
Maximum input size per file or stdin: 64 MiB.
";

#[derive(Debug)]
struct CliError {
    status: i32,
    message: String,
}
impl CliError {
    fn usage(message: &'static str) -> Self {
        Self { status: 2, message: message.to_owned() }
    }
    fn evidence(error: core::Error) -> Self {
        Self { status: 3, message: error.to_string() }
    }
    fn io() -> Self {
        Self { status: 4, message: "input/output operation failed".to_owned() }
    }
}

fn read_limited(path: &str) -> Result<Vec<u8>, CliError> {
    let mut content = Vec::new();
    if path == "-" {
        io::stdin().lock().take(MAX_INPUT + 1).read_to_end(&mut content)
            .map_err(|_| CliError::io())?;
    } else {
        File::open(path).map_err(|_| CliError::io())?
            .take(MAX_INPUT + 1)
            .read_to_end(&mut content)
            .map_err(|_| CliError::io())?;
    }
    if content.len() as u64 > MAX_INPUT {
        return Err(CliError::usage("input exceeds 64 MiB limit"));
    }
    Ok(content)
}

fn check_stdin_once(paths: &[&str]) -> Result<(), CliError> {
    if paths.iter().filter(|&&path| path == "-").count() > 1 {
        return Err(CliError::usage("standard input '-' may only be used once"));
    }
    Ok(())
}

fn parse_digest(text: &str) -> Result<[u8; 32], CliError> {
    core::parse_hex(text).map_err(|_| CliError::usage("expected 64 lowercase SHA-256 hex digits"))
}

/// Read a caller-selected, separately retained chain head. This file is
/// neither generated from nor automatically trusted because of the receipts.
/// Reject nonregular paths and keep all errors path-independent.
fn read_trusted_head_file(path: &str) -> Result<[u8; 32], CliError> {
    if path == "-" {
        return Err(CliError::usage("trusted-head file must be a regular file, not stdin"));
    }
    let metadata = std::fs::symlink_metadata(path).map_err(|_| CliError::io())?;
    if !metadata.file_type().is_file() {
        return Err(CliError::usage("trusted-head file must be a regular file"));
    }
    // Bound memory before checking syntax: exactly 64 lowercase ASCII hex
    // bytes, optionally terminated by one LF. No BOM/CR/extra whitespace.
    let mut bytes = Vec::new();
    File::open(path).map_err(|_| CliError::io())?
        .take(66).read_to_end(&mut bytes).map_err(|_| CliError::io())?;
    if bytes.last() == Some(&b'\n') { bytes.pop(); }
    if bytes.len() != 64 {
        return Err(CliError::usage("trusted-head file must contain 64 lowercase hex bytes, optionally LF"));
    }
    let hex = std::str::from_utf8(&bytes)
        .map_err(|_| CliError::usage("trusted-head file must contain lowercase ASCII hex"))?;
    parse_digest(hex)
}

fn previous(rest: &[String]) -> Result<Option<[u8; 32]>, CliError> {
    match rest {
        [] => Ok(None),
        [option, hex] if option == "--previous" => Ok(Some(parse_digest(hex)?)),
        _ => Err(CliError::usage("expected optional --previous <64-lowercase-hex>")),
    }
}

fn offset(text: &str) -> Result<usize, CliError> {
    if text.is_empty() || text.starts_with('+')
        || (text.len() > 1 && text.starts_with('0'))
        || !text.as_bytes().iter().all(u8::is_ascii_digit)
    {
        return Err(CliError::usage("byte-offset must be a nonnegative decimal integer"));
    }
    text.parse::<usize>().map_err(|_| CliError::usage("byte-offset is out of range"))
}

fn output(text: &str) -> Result<(), CliError> {
    let mut stdout = io::stdout().lock();
    stdout.write_all(text.as_bytes()).map_err(|_| CliError::io())?;
    stdout.write_all(b"\n").map_err(|_| CliError::io())?;
    stdout.flush().map_err(|_| CliError::io())
}

fn run(args: &[String]) -> Result<(), CliError> {
    if args.is_empty() || args[0] == "--help" || args[0] == "help" {
        return output(HELP);
    }
    core::check_abi().map_err(CliError::evidence)?;
    match args[0].as_str() {
        "hash" => {
            if args.len() != 2 { return Err(CliError::usage("hash requires exactly one input")); }
            let bytes = read_limited(&args[1])?;
            let digest = core::sha256(&bytes).map_err(CliError::evidence)?;
            let hex = core::to_hex(&digest).map_err(CliError::evidence)?;
            output(&format!(r#"{{"sha256":"{hex}","size":{}}}"#, bytes.len()))
        }
        "observe" => {
            if args.len() < 3 { return Err(CliError::usage("observe requires before and after")); }
            let prior = previous(&args[3..])?;
            check_stdin_once(&[&args[1], &args[2]])?;
            let before = read_limited(&args[1])?;
            let after = read_limited(&args[2])?;
            let evidence = core::observe(&before, &after).map_err(CliError::evidence)?;
            let receipt = core::create_receipt(&evidence, prior.as_ref()).map_err(CliError::evidence)?;
            output(&receipt.json().map_err(CliError::evidence)?)
        }
        "delete" => {
            if args.len() < 5 {
                return Err(CliError::usage("delete requires before, removed, after and byte-offset"));
            }
            let prior = previous(&args[5..])?;
            let at = offset(&args[4])?;
            check_stdin_once(&[&args[1], &args[2], &args[3]])?;
            let before = read_limited(&args[1])?;
            let removed = read_limited(&args[2])?;
            let after = read_limited(&args[3])?;
            let evidence = core::witness_delete(&before, &removed, &after, at)
                .map_err(CliError::evidence)?;
            let receipt = core::create_receipt(&evidence, prior.as_ref()).map_err(CliError::evidence)?;
            output(&receipt.json().map_err(CliError::evidence)?)
        }
        "verify" => {
            if args.len() != 2 { return Err(CliError::usage("verify requires one receipt")); }
            let json = read_limited(&args[1])?;
            let receipt = core::parse_receipt(&json).map_err(CliError::evidence)?;
            let hex = core::to_hex(&receipt.digest()).map_err(CliError::evidence)?;
            output(&format!(r#"{{"receipt_hash":"{hex}","self_hash_valid":true}}"#))
        }
        "verify-chain" => {
            if args.len() < 2 { return Err(CliError::usage("verify-chain requires receipt files")); }
            let mut end = args.len();
            let trusted = if end >= 4 && args[end - 2] == "--trusted-head" {
                end -= 2;
                Some(parse_digest(&args[end + 1])?)
            } else if end >= 4 && args[end - 2] == "--trusted-head-file" {
                end -= 2;
                Some(read_trusted_head_file(&args[end + 1])?)
            } else { None };
            if end <= 1 || args[1..end].iter()
                .any(|p| p == "--trusted-head" || p == "--trusted-head-file")
            {
                return Err(CliError::usage("verify-chain requires receipts followed by one optional trusted-head source"));
            }
            let paths: Vec<&str> = args[1..end].iter().map(String::as_str).collect();
            check_stdin_once(&paths)?;
            let mut receipts = Vec::with_capacity(paths.len());
            for path in paths {
                let input = read_limited(path)?;
                receipts.push(core::parse_receipt(&input).map_err(CliError::evidence)?);
            }
            core::verify_chain(&receipts, trusted.as_ref()).map_err(CliError::evidence)?;
            let head = core::to_hex(&receipts.last().expect("nonempty").digest())
                .map_err(CliError::evidence)?;
            let anchored = if trusted.is_some() { "true" } else { "false" };
            output(&format!(
                r#"{{"chain_valid":true,"count":{},"head":"{head}","trusted_head_checked":{anchored}}}"#,
                receipts.len(),
            ))
        }
        _ => Err(CliError::usage("unknown command; use --help")),
    }
}

fn main() {
    // env::args() panics when any Unix argument contains non-UTF-8 bytes,
    // and Rust's panic message can disclose the supplied pathname on stderr.
    // This version of the CLI explicitly supports only UTF-8 arguments;
    // reject others *without ever rendering their values*.
    let args: Vec<String> = match env::args_os()
        .skip(1)
        .map(|argument| argument.into_string())
        .collect::<Result<Vec<_>, _>>()
    {
        Ok(arguments) => arguments,
        Err(_) => {
            eprintln!("tombstone: command arguments must be valid UTF-8");
            process::exit(2);
        }
    };
    if let Err(error) = run(&args) {
        eprintln!("tombstone: {}", error.message);
        process::exit(error.status);
    }
}
