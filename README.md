<p align="center">
  <img alt="TOMBSTONE: cryptographic deletion receipts with a headstone and linked hashes" src="docs/assets/tombstone-banner.svg" width="950">
</p>

<p align="center">
  <strong>Cryptographic deletion-event receipts without archiving deleted content.</strong><br>
  <em>The data is gone from the receipt. The tombstone has a checksum.</em>
</p>

TOMBSTONE is a planned **C99-first** utility for deterministic, independently checkable evidence about file transitions and, when removed bytes are actually available to the tool, **explicit deletion events**.

**Project status: documentation and directory scaffolding only.** There is no working C engine, Rust CLI/TUI or GTK frontend yet. The machine-readable v1 schema is a **proposal**, not a released interface.

- **C99 logic**: byte handling, fingerprints, receipt encoding and verification.
- **Rust CLI + TUI**: automation and human interfaces using one C99 source of truth.
- **Optional GTK4**: later desktop GUI with no duplicated evidence logic.
- **Human prose**: root Markdown and [docs](docs/INDEX.md); **machine data**: [machine/](machine/README.md).

**Critical distinction:** A before/after SHA-256 comparison does **not** reveal what was deleted. An explicit deletion receipt requires access to the deleted bytes at the moment of the operation. Fingerprints are neither proof of secure erasure nor a way to recover lost bytes; predictable deleted data can be guessed from its hash.

Start with [GETTING_STARTED.md](GETTING_STARTED.md). See [ARCHITECTURE.md](ARCHITECTURE.md), [INVARIANTS.md](INVARIANTS.md), [AGENTS.md](AGENTS.md), [ROADMAP.md](ROADMAP.md), and [SECURITY.md](SECURITY.md).

A documentation/fixture smoke check (Python 3 standard library only) is available via \`make docs-check\`. It does not build the unimplemented product.

Existing repository license: [Apache-2.0](LICENSE).
