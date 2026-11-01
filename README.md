<p align="center">
  <img alt="TOMBSTONE: cryptographic deletion receipts with a headstone and linked hashes" src="docs/assets/tombstone-banner.svg" width="950">
</p>

<p align="center">
  <strong>Cryptographic deletion-event receipts without archiving deleted content.</strong><br>
  <em>The data is gone from the receipt. The tombstone has a checksum.</em>
</p>

TOMBSTONE is a **C99-first** project for deterministic, independently checkable evidence about file transitions and explicit caller-supplied deletion splices.

**Status:** Phases 0–4 are merged. **Phase 5 introduces an interactive Rust/ncurses terminal interface (pending PR review)** for human receipt inspection, chain verification and guided evidence creation. C99 remains authoritative for cryptography and all evidence decisions; the separate headless Rust CLI stays unchanged. GTK4 remains optional for Phase 6.

## Try the CLI

Requires Ubuntu C99 toolchain, OpenSSL development libraries and Rust/Cargo:

\`\`\`sh
sudo apt-get install build-essential pkg-config libssl-dev cargo rustc
cargo test -p tombstone-ffi -p tombstone-cli --locked --offline
cargo build -p tombstone-cli --release --locked --offline

target/release/tombstone hash tests/fixtures/before.txt
target/release/tombstone delete tests/fixtures/before.txt \
    tests/fixtures/deleted.txt tests/fixtures/after.txt 4
target/release/tombstone verify-chain \
    machine/examples/explicit-delete-v1.json \
    machine/examples/observed-transition-v1.json \
    machine/examples/unchanged-v1.json
\`\`\`

The chain command requires receipts in genesis-to-head order. Use the [CLI guide](docs/CLI.md) for an example with an independently trusted head.

The CLI emits deterministic machine-readable JSON to stdout, diagnostics to stderr, and nonzero exit codes on failure. It has no interactive prompts, no network operations, and **never deletes a file**.

## Interactive terminal UI (Phase 5)

On Ubuntu install `libncurses-dev` in addition to the CLI prerequisites. With an interactive terminal (not a pipeline):

```sh
cargo test --workspace --offline --locked
cargo build -p tombstone-tui --release --offline --locked
target/release/tombstone-tui
```

Choose one of five workflows with arrows, `j/k`, or keys `1`–`5`; inspect validated receipts, check entire chains, and optionally save canonical JSON to a **new** file with `s`. Nothing is overwritten or deleted. The TUI requires ncurses but **the C99 core and headless CLI do not**. See [TUI guide](docs/TUI.md).

## Validate the C99 core

\`\`\`sh
make test              # Phase 1–3 native tests
make sanitizer-test    # ASan + UBSan
make reproducibility   # deterministic static archives
make docs-check        # synthetic receipt fixture checks
\`\`\`

- [Rust ncurses TUI](docs/TUI.md)
- [Rust CLI and FFI](docs/CLI.md)
- [C99 receipt API](docs/RECEIPT_ENGINE.md)
- [Witnessed splice API](docs/DELETION_WITNESS.md)
- [SHA-256 API](docs/FINGERPRINT_API.md)
- [Architecture](ARCHITECTURE.md), [invariants](INVARIANTS.md), [agent instructions](AGENTS.md), [roadmap](ROADMAP.md), [security](SECURITY.md)

**Trust boundary:** A valid receipt asserts a cryptographically consistent *caller-supplied* splice, not authenticated proof of an actual edit, authorship, time or erasure. An unanchored chain can be rewritten wholesale; SHA-256 of guessable deleted data does not conceal that data.

Human prose is in root Markdown and \`docs/\`; the versioned machine contract is in \`machine/\`. License: [Apache-2.0](LICENSE).
