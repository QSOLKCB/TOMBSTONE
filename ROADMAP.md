# TOMBSTONE roadmap

**Phases 0 and 1 are merged and verified. Phase 2 implementation is proposed in this PR and requires review/CI before being considered complete.** Phases 3–7 remain unimplemented.

| Phase | Deliverable | Acceptance gate | Status |
| --- | --- | --- | --- |
| **0 — Foundation** | Human/machine docs, receipt proposal, adversarial fixtures, brand, structure | Documentation fixture checks | Merged |
| **1 — C99 fingerprinting** | OpenSSL EVP SHA-256, binary-safe streaming C ABI, vectors | GCC/Clang, sanitizers, reproducible archives | Merged, locally verified |
| **2 — C99 witnessed deletion** | Exact-splice verifier and independently classified transitions | Binary/NUL, repeated bytes, empty, replacement, offset/overflow, no mutation, GCC/Clang/sanitizers/reproducibility | In PR — review gate |
| **3 — Receipt serialization and chain** | Strict RFC 8785 canonical JSON v1, parser, receipt-link validation | Independent golden vectors, malformed keys, tampering | Planned |
| **4 — Rust CLI/FFI** | Safe FFI and deterministic machine CLI | Exact C parity, pipeline exit/status codes | Planned |
| **5 — Rust TUI** | Inspectable terminal workflow | Usable headless fallback, parity | Planned |
| **6 — Optional GTK4** | Thin desktop UI | No duplicated evidence computation | Planned |
| **7 — Hardening / release** | Fuzzing, cross-runtime/arch verification, optional external anchoring | Independent reviews and immutable tag | Planned |

## Phase 2 scope and exclusions

\`tb_observe_transition\` reports \`UNCHANGED\` or \`OBSERVED_TRANSITION\` after checking full input byte equality (not merely hash equality). Its deletion fields are zero.

\`tb_witness_delete\` requires a **nonempty removed span**, its claimed offset, before bytes and after bytes; it checks the byte-exact splice and produces fingerprint-only \`EXPLICIT_DELETE\` evidence. It does **not** infer deletion from snapshots, authenticate the offset's real-world origin, mutate filesystem content, retain removed plaintext, or produce a canonical receipt.

All C99 results are **in-memory evidence**, not Phase 3 JSON. Receipt v1 examples under \`machine/\` remain illustrative only.

## Subsequent PRs

1. Phase 3: strict RFC 8785 JSON receipt construction/parsing and hash chain verification, using the Phase 2 evidence object only after validation.
2. Phase 4: Rust FFI and noninteractive CLI, then the human TUI.
3. Phase 6+: optional GTK4 presentation, cross-platform hardening and release.

Licensing remains Apache-2.0; secure erasure, undisclosed plaintext recovery, authorship and timestamps remain outside the present design. Read [INVARIANTS.md](INVARIANTS.md) and [docs/DELETION_WITNESS.md](docs/DELETION_WITNESS.md).
