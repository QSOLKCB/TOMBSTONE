<p align="center">
  <img alt="TOMBSTONE: cryptographic deletion receipts with a headstone and linked hashes" src="docs/assets/tombstone-banner.svg" width="950">
</p>

<p align="center">
  <strong>Cryptographic deletion-event receipts without archiving deleted content.</strong><br>
  <em>The data is gone from the receipt. The tombstone has a checksum.</em>
</p>

TOMBSTONE is a **C99-first** project for deterministic, independently checkable evidence about file transitions and explicit caller-supplied deletion splices.

**Status:** Phases 0–3 are merged. **Phase 4 adds a Rust CLI and safe FFI adapter (pending PR review)**. The C99 core remains authoritative for all hashing, splice validation, receipt encoding/parsing and chain verification. Rust provides argument handling and presentation. A Rust TUI (Phase 5) and optional GTK4 GUI (Phase 6) are still planned.

## Try the CLI

Requires Ubuntu C99 toolchain, OpenSSL development libraries and Rust/Cargo:

\`\`\`sh
sudo apt-get install build-essential pkg-config libssl-dev cargo rustc
cargo test --workspace --locked --offline
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

## Validate the C99 core

\`\`\`sh
make test              # Phase 1–3 native tests
make sanitizer-test    # ASan + UBSan
make reproducibility   # deterministic static archives
make docs-check        # synthetic receipt fixture checks
\`\`\`

- [Rust CLI and FFI](docs/CLI.md)
- [C99 receipt API](docs/RECEIPT_ENGINE.md)
- [Witnessed splice API](docs/DELETION_WITNESS.md)
- [SHA-256 API](docs/FINGERPRINT_API.md)
- [Architecture](ARCHITECTURE.md), [invariants](INVARIANTS.md), [agent instructions](AGENTS.md), [roadmap](ROADMAP.md), [security](SECURITY.md)

**Trust boundary:** A valid receipt asserts a cryptographically consistent *caller-supplied* splice, not authenticated proof of an actual edit, authorship, time or erasure. An unanchored chain can be rewritten wholesale; SHA-256 of guessable deleted data does not conceal that data.

Human prose is in root Markdown and \`docs/\`; the versioned machine contract is in \`machine/\`. License: [Apache-2.0](LICENSE).
