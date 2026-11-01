<p align="center">
  <img alt="TOMBSTONE: cryptographic deletion receipts with a headstone and linked hashes" src="docs/assets/tombstone-banner.svg" width="950">
</p>

<p align="center">
  <strong>Cryptographic deletion-event receipts without archiving deleted content.</strong><br>
  <em>The data is gone from the receipt. The tombstone has a checksum.</em>
</p>

TOMBSTONE is a **C99-first** project for deterministic, independently checkable evidence about file transitions and explicit caller-witnessed deletion splices.

**Implementation status:** Phases 0–2 are merged. **Phase 3 is implemented in a reviewable PR**, introducing deterministic canonical JSON v1 receipts, strict parsing, hash verification and optional externally anchored chain verification. No filesystem deletion, Rust CLI/TUI, or GTK exists yet. The receipt contract remains subject to Phase 3 review.

- **C99 engine:** OpenSSL EVP SHA-256 (Phase 1), exact-splice witnessing and observed transitions (Phase 2), and canonical receipts/chain verification (Phase 3).
- **Evidence boundary:** a verified splice establishes a mathematical relationship among supplied buffers—not who performed an edit, whether it happened historically, or whether bytes were securely erased.
- **Rust CLI + TUI:** planned agent/human interfaces; **GTK4** remains optional.
- **Document separation:** human prose in root Markdown and [docs](docs/INDEX.md), machine schemas/examples in [machine/](machine/README.md).

## Build and test

Requires C99 compiler, GNU Make, GNU ar, pkg-config, and OpenSSL development libraries (Ubuntu: \`build-essential pkg-config libssl-dev\`).

\`\`\`sh
make                  # build/libtombstone.a
make test             # SHA-256, splice, canonical receipts, malformed/chain cases
make sanitizer-test   # ASan + UBSan (GCC)
make reproducibility  # compare two independent deterministic static archives
make docs-check       # original machine receipt toy fixtures (not a verifier)
\`\`\`

Public headers: [fingerprint.h](include/tombstone/fingerprint.h), [deletion.h](include/tombstone/deletion.h), [receipt.h](include/tombstone/receipt.h). See the [Phase 3 receipt API](docs/RECEIPT_ENGINE.md). See [Phase 2 API guide](docs/DELETION_WITNESS.md), [fingerprint API](docs/FINGERPRINT_API.md), and [getting started](GETTING_STARTED.md).

**Privacy warning:** SHA-256 is not encryption. Fingerprints of short, guessable removed data can be brute-forced. No real deleted content is retained in the output evidence structure; callers are responsible for their own buffers, editor histories and backups.

Governance: [ARCHITECTURE.md](ARCHITECTURE.md), [INVARIANTS.md](INVARIANTS.md), [AGENTS.md](AGENTS.md), [ROADMAP.md](ROADMAP.md), [SECURITY.md](SECURITY.md). License: [Apache-2.0](LICENSE).
