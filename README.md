<p align="center">
  <img alt="TOMBSTONE: cryptographic deletion receipts with a headstone and linked hashes" src="docs/assets/tombstone-banner.svg" width="950">
</p>

<!-- Live GitHub Actions status: these badges report the latest main-branch workflow results. -->
<p align="center">
  <a href="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/c99-fingerprint.yml"><img alt="C99 core — GCC, Clang and sanitizers" src="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/c99-fingerprint.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/rust-cli.yml"><img alt="Rust CLI and C99 FFI" src="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/rust-cli.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/rust-tui.yml"><img alt="ncurses TUI and terminal checks" src="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/rust-tui.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/rust-gtk.yml"><img alt="GTK4 desktop and D-Bus smoke" src="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/rust-gtk.yml/badge.svg?branch=main"></a>
</p>
<p align="center">
  <a href="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/hardening.yml"><img alt="Clang fuzzing, sanitizers and architecture replay" src="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/hardening.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/docs-check.yml"><img alt="Schema, receipts and documentation" src="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/docs-check.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/release-candidate.yml"><img alt="Reproducible source candidate and SHA-256 manifest" src="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/release-candidate.yml/badge.svg?branch=main"></a>
</p>
<p align="center">
  <a href="https://github.com/QSOLKCB/TOMBSTONE/releases/tag/v0.1.0"><img alt="Release v0.1.0" src="https://img.shields.io/github/v/release/QSOLKCB/TOMBSTONE?style=flat-square"></a>
  <a href="LICENSE"><img alt="Apache-2.0 license" src="https://img.shields.io/github/license/QSOLKCB/TOMBSTONE?style=flat-square"></a>
</p>

<p align="center">
  <strong>Cryptographic deletion-event receipts without archiving deleted content.</strong><br>
  <em>The data is gone from the receipt. The tombstone has a checksum.</em>
</p>

TOMBSTONE is a C99-first system for deterministic, independently checkable fingerprints of caller-supplied bytes, exact deletion-splice relationships and linked canonical receipt evidence.

**Status:** [v0.1.0 — Initial Public Release](https://github.com/QSOLKCB/TOMBSTONE/releases/tag/v0.1.0), with Phases 0–7 merged, bounded C99 fuzzing, independent GCC/Clang and Linux x86-64/ARM64 receipt replay, and [reproducible source release evidence](docs/release/v0.1.0/POST_MERGE_EVIDENCE.md). C99 alone owns SHA-256, witnessed-splice validation, canonical receipt encoding and chain verification; Rust supplies the CLI, TUI and optional GTK4 desktop. Verification is not security certification, historical deletion attestation or secure erasure.

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

## Phase 9 — Source-level C99 proof obligations

The **production** C99 byte-splice relation now carries an ACSL contract with quantified equality over arbitrary valid buffer lengths and loop invariants. [Frama-C/WP](docs/FORMAL_VERIFICATION.md) checks its actual source code; the [Phase 9 CI verification](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41305390928) discharged **35/35 proof goals** on the production helper. The CI gate requires every generated nonzero obligation to be proved. This does **not** yet prove the entire public C99 wrapper, OpenSSL, compiled machine code or historical deletion events. Published `v0.1.0` remains immutable.

## Phase 7 hardening checks

Run the bounded sanitizer-backed C99 fuzzers and use the GitHub Actions x86-64/ARM64 matrix for independent replay:

```sh
make fuzz               # Clang libFuzzer, AddressSanitizer and UBSan
```

The [release gate](docs/RELEASE_GATE.md), [v0.1.0 evidence record](docs/release/v0.1.0/POST_MERGE_EVIDENCE.md), [anchoring/privacy notes](docs/ANCHORING_PRIVACY.md) and [portability matrix](docs/PORTABILITY.md) document the completed checks and their limits. These tests do not prove deletion, confidentiality or erasure.

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
