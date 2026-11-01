# TOMBSTONE roadmap

**Phases 0–2 are merged and verified. Phase 3 is implemented in a PR pending exact-head review and CI.** Phases 4–7 remain unimplemented.

| Phase | Deliverable | Acceptance gate | Status |
| --- | --- | --- | --- |
| **0 — Foundation** | Human/machine docs, receipt proposal, adversarial fixtures, brand, structure | Documentation fixture checks | Merged |
| **1 — C99 fingerprinting** | OpenSSL EVP SHA-256, binary-safe streaming C ABI, vectors | GCC/Clang, sanitizers, reproducible archives | Merged, locally verified |
| **2 — C99 witnessed deletion** | Exact-splice verifier and independently classified transitions | Binary/NUL, repeated bytes, empty, replacement, offset/overflow, no mutation, GCC/Clang/sanitizers/reproducibility | Merged and locally verified |
| **3 — Receipt serialization and chain** | Schema-limited RFC 8785 canonical JSON v1, strict parser, receipt-link validation | Existing golden receipts, malformed/duplicate inputs, tampering, anchoring, sanitizers | Implemented in PR; CI/review gate |
| **4 — Rust CLI/FFI** | Safe FFI and deterministic machine CLI | Exact C parity, pipeline exit/status codes | Planned |
| **5 — Rust TUI** | Inspectable terminal workflow | Usable headless fallback, parity | Planned |
| **6 — Optional GTK4** | Thin desktop UI | No duplicated evidence computation | Planned |
| **7 — Hardening / release** | Fuzzing, cross-runtime/arch verification, optional external anchoring | Independent reviews and immutable tag | Planned |

## Phase 2 scope and exclusions

\`tb_observe_transition\` reports \`UNCHANGED\` or \`OBSERVED_TRANSITION\` after checking full input byte equality (not merely hash equality). Its deletion fields are zero.

\`tb_witness_delete\` requires a **nonempty removed span**, its claimed offset, before bytes and after bytes; it checks the byte-exact splice and produces fingerprint-only \`EXPLICIT_DELETE\` evidence. It does **not** infer deletion from snapshots, authenticate the offset's real-world origin, mutate filesystem content, retain removed plaintext, or produce a canonical receipt.

Phase 3 accepts the Phase 2 **in-memory evidence**, serializes a canonical digest-bearing JSON receipt, parses receipt bytes and verifies chains. Preexisting machine examples are now regression/golden vectors rather than documentation-only placeholders.

## Subsequent PRs

1. Phase 4: Rust FFI and noninteractive CLI calling the C99 core; then the human TUI.
3. Phase 6+: optional GTK4 presentation, cross-platform hardening and release.

Licensing remains Apache-2.0; secure erasure, undisclosed plaintext recovery, authorship and timestamps remain outside the present design. Read [INVARIANTS.md](INVARIANTS.md) and [docs/DELETION_WITNESS.md](docs/DELETION_WITNESS.md).
