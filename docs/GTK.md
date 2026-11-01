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

## Multi-instance activation safety

GTK routes a second process launch to the existing application. Its activation handler now presents the existing GtkApplication window rather than building another window or overwriting the shared widget pointers. When no window exists, a new one can be constructed. The `--smoke-test` path performs a second application activation on the GTK main loop and verifies that exactly one window exists and the existing-window branch executed, in addition to the C99 fingerprint check. This avoids cross-window input confusion and potential use-after-free when windows are closed out of order.

## Second-launch behavior on Wayland

GTK4 forwards another process's activation to the running instance through the session D-Bus when application uniqueness is available. The activation handler reuses its one live window and calls `gtk_window_present()`. **This is a request, not a guarantee of keyboard focus.** GNOME/Mutter on Wayland may deny a programmatically initiated focus or raise operation, particularly from another terminal. A successful second launch may therefore exit immediately without visibly focusing the window. Users can select the existing window in the Activities overview or task switcher.

The GTK CI suite now includes a separate, explicit **two-process** test under an isolated D-Bus session and Xvfb. It verifies that a secondary invocation reaches the first process and retains one window. The in-process `--smoke-test` still independently checks callback reuse. Neither test asserts compositor-granted focus on a real Wayland session.
