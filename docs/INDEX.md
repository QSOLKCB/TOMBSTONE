# Human documentation index

All files here are human-readable explanations. The machine-readable contract and examples live separately in [machine/](../machine/README.md).

- [Phase 7 release gate](RELEASE_GATE.md) — mandatory exact-head, CI and asset evidence before immutable tag
- [Independent portability](PORTABILITY.md) — GCC/Clang and Linux x86-64/ARM64 replay scope
- [Anchoring and privacy](ANCHORING_PRIVACY.md) — local-chain, short-secret and erasure limitations
- [Optional GTK4 desktop](GTK.md) — Phase 6 native interface, build isolation and privacy boundary
- [Rust ncurses TUI](TUI.md) — Phase 5 guided human inspection and verification, C99 interface boundary
- [Rust CLI and FFI](CLI.md) — Phase 4 headless commands, statuses, C99 boundary and trust limits
- [C99 receipt engine](RECEIPT_ENGINE.md) — Phase 3 canonical JSON, strict parser and SHA-256 chains
- [C99 witnessed deletion API](DELETION_WITNESS.md) — Phase 2 exact splice vs snapshot comparison
- [C99 fingerprint API](FINGERPRINT_API.md) — Phase 1 public SHA-256 ABI, usage, errors and backend
- [Architecture](../ARCHITECTURE.md) — C99 evidence core, Rust CLI/TUI, optional GTK
- [Invariants](../INVARIANTS.md) — testable requirements
- [Roadmap](../ROADMAP.md) — phased, evidence-gated delivery
- [Getting started](../GETTING_STARTED.md) — available documentation checks
- [Security](../SECURITY.md) — nonclaims, exposure and privacy
- [Concept and terminology](CONCEPT.md) — what a deletion receipt means
- [Receipt format](RECEIPT_FORMAT.md) — candidate wire contract explained
- [Threat model](THREAT_MODEL.md) — explicit trust boundaries and attacks
- [Decision 0001](decisions/0001-c99-core-rust-frontends.md) — why this stack
- [Brand asset](assets/tombstone-banner.svg) — README header graphic

**Human-facing text is not the machine protocol.** Treat the versioned schema under \`machine/\` as the design proposal pending implementation and release.
