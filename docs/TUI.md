# Phase 5 — interactive Rust terminal interface

**Status:** Implementation in the Phase 5 PR, pending exact-head review. The new `tombstone-tui` is a Rust frontend backed by system **ncursesw**, the existing safe Rust FFI adapter and the authoritative **C99 evidence engine**. No third-party Rust crates, cloud services, telemetry or Node.js.

## Ubuntu setup

```sh
sudo apt-get install build-essential pkg-config libssl-dev libncurses-dev rustc cargo
cargo test --workspace --locked --offline
cargo build -p tombstone-tui --release --locked --offline
target/release/tombstone-tui
```

Run in an interactive terminal with TERM configured (Ptyxis, xterm, etc.). The program **rejects non-TTY invocations**, so use the separately provided headless `tombstone` CLI for agents and pipes. `tombstone-tui --help` works without a TTY. C99 and the headless CLI have no ncurses runtime dependency.

## Workflows and keys

The menu offers five actions:

1. SHA-256 fingerprint of a selected file
2. Compare before and after bytes, producing observed-transition or unchanged evidence without inferring removed bytes
3. Verify an explicit deletion using before, removed, after and byte offset, then create canonical C99 receipt
4. Inspect one receipt's validity and self-hash (not its chain)
5. Verify 1–64 **ordered** receipts from genesis, optionally against an external trusted final hash

`j`/`k` or Up/Down move, Enter runs a selection, keys 1–5 select menu items, `h` shows help, `q` exits. On results, `j`/`k` scroll, `b`/Enter returns, and `s` prompts for an explicit save **only when a canonical receipt is available**. Saving creates a new file (never overwrites), writes only canonical JSON plus newline, and uses mode 0600 on Unix. No receipts are automatically persisted. Entering `~` cancels prompts without changing files.

For generated receipts, leaving the predecessor prompt blank creates genesis. Entering 64 lowercase hex digits links a **caller-supplied** previous digest. This does **not** verify the previous receipt; use the full ordered chain workflow, with an independently retained trusted head if required.

## Privacy and limits

The display filters control characters. User-provided file paths do not appear in reports, canonical JSON or error messages; they appear only while the user types in a prompt and are cleared afterward. The TUI accepts UTF-8 prompt paths, reads up to 64 MiB per data file and 16 KiB per receipt, and limits full chains to 64 receipts. File contents themselves are binary-safe.

The engine cannot erase data, validate historic authorship/time, or recover deleted plaintext. Secret source bytes may survive in files, process memory, swap, editors and backups; short hashes are vulnerable to dictionary guessing. A mathematically verified splice is not an authenticated historical deletion, and a locally consistent chain can be rewritten wholesale without an external trusted anchor.

## Verification

`cargo test --workspace --locked --offline` runs C99 parity, golden receipt, invalid splice, chain-order, privacy and noninteractive terminal regression tests. A Linux GitHub Actions job builds the TUI and checks the no-TTY failure path; original GCC/Clang and CLI jobs remain enabled. GTK stays in Phase 6.
