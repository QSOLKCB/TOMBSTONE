# Invariants — design requirements

**Status:** Phase 1 implements TMB-001 and Phase 2 implements the **in-memory byte verification portions** of TMB-002–005, TMB-009 and TMB-014, pending review. Durable receipt and chain requirements remain for Phase 3. \`make docs-check\` checks illustrative fixtures, not the real engine; \`make test\`, \`make sanitizer-test\` and \`make reproducibility\` exercise the new library.

| ID | Requirement | Required future validation |
| --- | --- | --- |
| TMB-001 | Hash exact bytes including NUL, whitespace and newlines. | SHA-256 vectors, binary fixtures |
| TMB-002 | Before/after hashes alone never identify removed bytes. | Negative transition tests |
| TMB-003 | \`explicit-delete\` requires witnessed before, after, deleted bytes and byte offset, with exact splice equality. | Adversarial splice tests |
| TMB-004 | \`observed-transition\` and \`unchanged\` have \`deleted: null\`; no deletion is inferred from a diff. | Condition checks |
| TMB-005 | Unchanged files have equal byte count and fingerprint. No-op never becomes a deletion. | No-op test |
| TMB-006 | Receipt serialization omits deleted plaintext, paths and arbitrary identifying metadata. | Serialization audit |
| TMB-007 | \`receipt_hash\` is SHA-256 over the domain prefix plus RFC 8785 canonical JSON minus \`receipt_hash\`. | C/Rust parity |
| TMB-008 | A non-genesis \`previous_receipt_hash\` points to its exact predecessor; external anchoring is out of scope. | Reordering, substitution tests |
| TMB-009 | All sizes and byte offsets are nonnegative and overflow checked. | 32-/64-bit boundary tests |
| TMB-010 | Duplicate keys, extra fields, malformed receipts and unknown versions are rejected. | Parser negative corpus |
| TMB-011 | C99 owns receipt logic; Rust TUI/CLI and optional GTK cannot silently fork evidence semantics. | Cross-interface parity |
| TMB-012 | Agent/CLI JSON output is deterministic and prompt-free; diagnostics go to stderr. | Pipeline integration tests |
| TMB-013 | Receipts assert neither secure erasure nor authorship nor independently proven chronology. | API/UX review |
| TMB-014 | The SHA-256 empty-input digest is valid but never by itself evidence of a deletion. | Empty vs no-op tests |
| TMB-015 | A chain can be rewritten in full without a trusted external anchor. | Threat model and anchoring checks |

**Boundary:** JSON Schema handles syntax and basic conditional structure, not splice equality, signature authenticity, hash correctness, or chain integrity. Phase 2 tests byte-exact splice relationships and reports `TB_ERR_MISMATCH` on false witnesses; Phase 3 still needs executable receipt and chain checks. A historical diff must never be promoted to a witnessed deletion.
