<p align="center">
  <img alt="TOMBSTONE: cryptographic deletion receipts with a headstone and linked hashes" src="docs/assets/tombstone-banner.svg" width="950">
</p>

<p align="center">
  <strong>Cryptographic deletion-event receipts without archiving deleted content.</strong><br>
  <em>The data is gone from the receipt. The tombstone has a checksum.</em>
</p>

TOMBSTONE is a C99-first system for deterministic, independently checkable fingerprints of caller-supplied bytes, exact deletion-splice relationships and linked canonical receipt evidence.

**Status:** Phases 0–6 are merged. **Phase 7 adds bounded C99 fuzzing, independent cross-compiler/architecture receipt replay, and a release evidence gate (pending PR review).** C99 alone owns SHA-256, witness validation, canonical receipt encoding and chain verification; Rust handles terminal and desktop interfaces. No immutable tag or security certification is created by this PR.

## Interfaces

| Interface | Build | Runtime requirements |
| --- | --- | --- |
| Native C99 core | `make test` | C99 + OpenSSL |
| Headless Rust CLI | `cargo build -p tombstone-cli --release --offline --locked` | Rust, OpenSSL |
| ncurses Rust TUI | `cargo build -p tombstone-tui --release --offline --locked` | Rust, ncurses |
| Optional GTK4 GUI | `cargo build --manifest-path apps/gtk/Cargo.toml --release --offline --locked` | Rust, GTK4 |

### GTK4 desktop (Ubuntu)

```sh
sudo apt-get install build-essential pkg-config libssl-dev libgtk-4-dev cargo rustc
cargo test --manifest-path apps/gtk/Cargo.toml --offline --locked
cargo build --manifest-path apps/gtk/Cargo.toml --release --offline --locked
apps/gtk/target/release/tombstone-gtk
```

The GUI offers fingerprint, observed-transition, witnessed-deletion, receipt inspection, chain verification and **explicit create-new receipt export**, using the same tested C99-backed workflows as the TUI. The **root Cargo workspace excludes GTK**, preserving all headless builds and tests.

## Phase 7 hardening checks

Run the bounded sanitizer-backed C99 fuzzers and use the GitHub Actions x86-64/ARM64 matrix for independent replay:

```sh
make fuzz               # Clang libFuzzer, AddressSanitizer and UBSan
```

The [release gate](docs/RELEASE_GATE.md), [anchoring/privacy notes](docs/ANCHORING_PRIVACY.md) and [portability matrix](docs/PORTABILITY.md) explain the evidence required before any immutable tag. These tests do not prove deletion, confidentiality or erasure.

## Verify the engine and existing interfaces

```sh
make test
make sanitizer-test
make reproducibility
make docs-check
cargo test --workspace --locked --offline
```

Read the [Phase 7 release gate](docs/RELEASE_GATE.md), [GTK4 guide](docs/GTK.md), [TUI guide](docs/TUI.md), [CLI guide](docs/CLI.md), [architecture](ARCHITECTURE.md), [roadmap](ROADMAP.md), [invariants](INVARIANTS.md), and [security](SECURITY.md).

Human prose lives in root Markdown and `docs/`; machine-readable receipts/schemas and synthetic fixtures live in `machine/`. [Apache-2.0](LICENSE).

**Trust limits:** A valid supplied byte-splice relationship is not proof that a deletion historically took place or that data was securely erased. A local-only chain can be rewritten without an independently trusted head; SHA-256 of guessable plaintext is not confidential.
