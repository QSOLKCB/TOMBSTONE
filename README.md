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
  <a href="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/phase20-receipt-prerequisites.yml"><img alt="Phase 20 — receipt contracts and model canaries" src="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/phase20-receipt-prerequisites.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/release-candidate.yml"><img alt="Frozen v0.1.0 source archive and checksum continuity" src="https://github.com/QSOLKCB/TOMBSTONE/actions/workflows/release-candidate.yml/badge.svg?branch=main"></a>
</p>
<p align="center">
  <a href="https://github.com/QSOLKCB/TOMBSTONE/releases/tag/v0.2.0"><img alt="Release v0.2.0" src="https://img.shields.io/github/v/release/QSOLKCB/TOMBSTONE?style=flat-square"></a>
  <a href="https://doi.org/10.5281/zenodo.23876710"><img alt="Zenodo DOI: v0.2.0 formal verification and release evidence" src="https://zenodo.org/badge/DOI/10.5281/zenodo.23876710.svg"></a>
  <a href="LICENSE"><img alt="Apache-2.0 license" src="https://img.shields.io/github/license/QSOLKCB/TOMBSTONE?style=flat-square"></a>
</p>

<p align="center">
  <strong>Cryptographic deletion-event receipts without archiving deleted content.</strong><br>
  <em>The data is gone from the receipt. The tombstone has a checksum.</em>
</p>

TOMBSTONE is a C99-first system for deterministic, independently checkable fingerprints of caller-supplied bytes, exact deletion-splice relationships and linked canonical receipt evidence.

**Current release:** [v0.2.0 — C99 Proofs & Verified Toolchain Reuse](https://github.com/QSOLKCB/TOMBSTONE/releases/tag/v0.2.0), published immutably at [`881e7db`](https://github.com/QSOLKCB/TOMBSTONE/commit/881e7db29054a02273b0e924b08409a777ce42ea). All **21 post-merge workflows** passed on that release commit. The release brings together the verification work introduced across Phases 8–20, an optional HACL* SHA2-256 backend, externally retained chain heads, and the first OPT-inspired toolchain reuse implementation. Remaining proof obligations are explicit; the programme is not an end-to-end verification of every dependency.

C99 alone owns hashing, witnessed-splice validation, canonical receipt encoding and chain verification; Rust supplies the CLI, TUI and optional GTK4 desktop. The engine works offline, and receipt output contains digests and metadata without archiving the supplied plaintext. Verification is not security certification, historical deletion attestation or secure erasure.

## Interfaces

| Interface | Build | Runtime requirements |
| --- | --- | --- |
| Native C99 core | `make test` | C99 + OpenSSL by default; optional HACL* backend |
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

### Optional HACL* SHA2-256 backend

OpenSSL remains the default. To check the vendored source identities and test the optional HACL* backend:

```sh
python3 tools/check_hacl_source.py
make SHA256_BACKEND=hacl test
TOMBSTONE_SHA256_BACKEND=hacl cargo test --workspace --offline --locked
```

The backend uses immutable upstream source and preserves the existing C99 API and receipt bytes. Upstream HACL* proofs do not automatically verify TOMBSTONE's adapter, allocation/lifetime handling or compiled executable. See [provider provenance and remaining refinement work](docs/PHASE13_HACL.md).

### Check an independently retained chain head

```sh
target/release/tombstone verify-chain receipt-1.json receipt-2.json \
  --trusted-head-file trusted-head.txt
```

Supply receipts in genesis-to-head order. The head file must contain exactly 64 lowercase hexadecimal digits, optionally followed by one LF. On the supported Linux targets, the reader rejects final-component symlinks, nonregular files and malformed contents. The head must come from an independently trusted source; a digest copied from the chain being checked does not establish independent trust. See [target and anchor boundaries](docs/PHASE16_TARGET_TRUST.md).

## Verification included in v0.2.0

Verification targets actual production source or overlays that must reproduce its exact bytes. CI distinguishes bounded symbolic checks, conditional deductive proofs and native execution evidence. Failed attempts remain recorded; missing, zero-goal, partial or misidentified proof results cannot be promoted to acceptance.

| Work | Evidence and scope |
| --- | --- |
| **Phases 8–11: witnessed-byte relationships and witness API** | Bounded direct-source CBMC checks, unbounded splice and prehash contracts, and modular witness-wrapper WP evidence under explicit SHA-provider/model premises. [Foundations](docs/FORMAL_VERIFICATION.md) · [Wrapper scope](docs/PHASE11_WRAPPER.md) |
| **Phases 12–13: provider boundary** | Actual OpenSSL failure injection, source-pinned HACL* integration, bounded adapter checks and provider parity. Real SHA-provider refinement remains open. [Assumption ledger](docs/ASSUMPTION_LEDGER.md) · [HACL*](docs/PHASE13_HACL.md) |
| **Phases 14–17: receipts, ABI and anchors** | Decimal/duplicate-field contracts, bounded parser and chain-rejection checks, C99/Rust ABI comparisons, independent executable rebuilds, and external-head tests on supported Linux targets. [Receipts](docs/PHASE14_RECEIPTS.md) · [ABI](docs/PHASE15_ABI.md) · [Chain checks](docs/PHASE17_CHAIN.md) |
| **Phases 18–19: chain and helper refinement** | Unbounded conditional chain verification, actual equality/hash helpers, and a separate caller-memory ownership composition that preserves the original Phase 18 theorem. [Chain theorem](docs/PHASE18_CHAIN_WP.md) · [Helpers](docs/PHASE19_HELPERS.md) · [Composition](docs/PHASE19_BRIDGE.md) |
| **Phase 20: validator and formatter prerequisites** | **1,392/1,392 positive WP/runtime-error obligations**, three designated semantic negative controls, and original Phase 18/19 theorem replays using an explicitly corrected Bytes model. Formatter framing, bounds and termination do not establish full canonical-JSON contents. [Contracts](docs/PHASE20_RECEIPT_PREREQUISITES.md) · [Model correction](docs/PHASE20_MODEL_CORRECTION.md) |

The [reviewed PR-head Phase 20 run](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41389325046) passed **14/14 jobs**, including unchanged original theorem replays of **54/54, 11/11, 40/40 and 41/41** goals. The [post-merge Phase 20 run](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41391635022) also passed on the v0.2.0 release source. These are recorded results for identified commits; live badges above describe the latest `main` runs.

The corrected-model gate reproduces the original Bytes-theory contradiction, rejects the false claims under the isolated correction, and executes positive refutations, 48 affected library subgoals, readonly controls and a string-witness lemma. This is regression evidence and conditional source verification, not a general soundness proof of Frama-C, Why3 or Alt-Ergo.

## Verified toolchain reuse

The first OPT rollout restores one independently pinned corrected WP build only after checking its producer, effective build/policy inputs, ZIP/tar digests and complete file manifest. Changed inputs or unavailable approved artifacts require a cold build; integrity or provenance failures stop the job. The workflow's manual `force_cold` input bypasses reuse.

**Every canary and proof still executes afresh. Proof-result caching remains disabled.** The implementation adds **34 reuse/replay-binding tests** alongside the existing **117 evidence-tamper checks**, without rewriting historical proof records.

Three cold/reuse pairs in the [executed benchmark](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41389325039) measured:

| Preparation mode | Median preparation plus fresh canaries |
| --- | ---: |
| Cold build | 65.469 seconds |
| Verified reuse | 54.044 seconds |

That is **11.425 seconds saved (17.45%)** for this stage on one Ubuntu 24.04 AMD64 runner. Shared container-image download time is excluded; these measurements do not represent whole-CI speedup or Actions cache-service latency. See [identities, measurement method and rollback](docs/PHASE20_TOOLCHAIN_REUSE.md).

## Hardening and local checks

Run the bounded sanitizer-backed C99 fuzzers and use the GitHub Actions x86-64/ARM64 matrix for independent replay:

```sh
make fuzz               # Clang libFuzzer, AddressSanitizer and UBSan
```

Other local checks:

```sh
make test
make sanitizer-test
make reproducibility
make docs-check
cargo test --workspace --locked --offline
```

The public C99 ABI and frozen v1 receipt fixtures are preserved. The immutable [v0.1.0 release](https://github.com/QSOLKCB/TOMBSTONE/releases/tag/v0.1.0) and its [source evidence](docs/release/v0.1.0/POST_MERGE_EVIDENCE.md) remain available. The source-candidate workflow intentionally rebuilds that historical v0.1.0 archive; it does not package v0.2.0 assets.

## Remaining proof and trust boundaries

Actual SHA-provider refinement, complete canonical-JSON/parser semantics, concrete backend allocation/lifetime guarantees, Rust ownership/FFI refinement and source-to-executable correctness remain open. The separate Phase 19 caller-memory result does not close the original literal global-frame obligation. Libc effects, model separation, compiler behaviour and OS/hardware reliability remain stated premises. See the [assumption ledger](docs/ASSUMPTION_LEDGER.md), [Phase 20 scope](docs/PHASE20_RECEIPT_PREREQUISITES.md) and [issue #28](https://github.com/QSOLKCB/TOMBSTONE/issues/28).

A valid supplied byte-splice relationship does not prove that a deletion historically occurred or that data was securely erased. An unanchored chain can be rewritten wholesale, and SHA-256 commitments to short or predictable plaintext are susceptible to guessing. Receipts do not authenticate identity or time. See [anchoring and privacy](docs/ANCHORING_PRIVACY.md), [portability limits](docs/PORTABILITY.md) and [security](SECURITY.md).

Read the [getting-started guide](GETTING_STARTED.md), [CLI guide](docs/CLI.md), [TUI guide](docs/TUI.md), [GTK4 guide](docs/GTK.md), [documentation index](docs/INDEX.md), [architecture](ARCHITECTURE.md), [roadmap](ROADMAP.md), [invariants](INVARIANTS.md), and [release gate](docs/RELEASE_GATE.md).

Human prose lives in root Markdown and `docs/`; machine-readable receipts/schemas and synthetic fixtures live in `machine/`. [Apache-2.0](LICENSE).
