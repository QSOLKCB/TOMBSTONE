# Phase 6 — optional GTK4 desktop application

**Status:** Proposed in Phase 6 PR, subject to exact-head review. `apps/gtk/` is a separate Rust Cargo workspace that calls system GTK4 through narrow UI-only Rust FFI. It reuses the **Phase 5 tested Rust workflows**, which call the C99 engine through `tombstone-ffi`. GTK never calculates hashes, verifies splices or canonicalizes receipts.

GTK is not required to build the C99 library, headless CLI or ncurses TUI. The root Cargo workspace explicitly excludes `apps/gtk`.

## Ubuntu setup

```sh
sudo apt-get install build-essential pkg-config libssl-dev libgtk-4-dev cargo rustc
cargo test --manifest-path apps/gtk/Cargo.toml --locked --offline
cargo build --manifest-path apps/gtk/Cargo.toml --release --locked --offline
apps/gtk/target/release/tombstone-gtk
```

The desktop GUI respects the system GTK theme (including Yaru-dark). It does not install a service or access the network. `--help` does not need a display; `--smoke-test` needs a display and is run in Xvfb by CI to test startup and C99 SHA-256 access.

## Six desktop tabs

- **Fingerprint:** SHA-256 of bytes from a caller-selected path.
- **Observe:** compare two file buffers, producing observed-transition or unchanged evidence (never inferred deletion); optional predecessor digest.
- **Witness deletion:** supply before, removed and after file paths, a byte offset and optional predecessor, then verify the exact splice.
- **Inspect receipt:** check one receipt's self-hash only (not its history).
- **Verify chain:** provide 1–64 paths in *genesis-to-head* order separated by a vertical bar `|` and an optional independently trusted final head. The initial input field cannot express a path containing `|`.
- **Save receipt:** explicit create-new-only export of the last successfully generated/inspected canonical JSON. No auto-save, no overwrite. Failed/new evidence attempts clear the prior export state.

The report area is read-only and cannot modify input files.

## Boundaries and tests

Source bytes remain binary-safe and are limited by the shared workflow layer to 64 MiB per input, 16 KiB per receipt, 64 receipts per chain. Path entry is UTF-8 and visible **while typed** but names and plaintext do not appear in canonical receipt output or sanitized errors. On Unix, saved files use mode 0600. Receipts do not prove secure erasure, historical actions, author identity or time. Locally consistent chains can be rewritten wholesale unless their final hash is independently anchored. Short deleted-data hashes may be guessed.

Linux CI checks GTK build/activation in Xvfb, original golden receipt hashes, C99 parity, anchored/reordered-chain rejection, create-new save and non-UTF-8 argument privacy. CLI/TUI/C99 workflows remain independently runnable without GTK.

See [architecture](../ARCHITECTURE.md), [security](../SECURITY.md) and [roadmap](../ROADMAP.md).
