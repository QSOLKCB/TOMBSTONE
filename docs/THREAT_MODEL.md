# Threat model (initial draft)

## Protected goals

- Preserve integrity of *recorded* byte fingerprints and chain relationships.
- Avoid storing plaintext deleted data *inside receipts*.
- Distinguish eyewitness deletion from comparison-only transitions.

## Adversaries and limitations

| Threat | Mitigation / limitation |
| --- | --- |
| Someone edits or swaps a receipt | Canonical body digest detects modification relative to an independently trusted receipt hash |
| Entire local chain is replaced | **Not prevented** without external anchoring, signatures or independent copies |
| A receipt fabricates a deletion | Hashes alone cannot prove the asserted bytes were truly removed; trust in operation boundary is required |
| A file snapshot appears to show deleted text | Snapshot comparison supports an observed transition, never an authoritative deletion span |
| User's removed text is a short predictable secret | Bare SHA-256 is susceptible to dictionary guesses; v1 cannot promise confidentiality |
| Removed data remains in swap, backups, editor undo history, journal | No secure erasure guarantee, only receipt-content minimization |
| C99 parsing is attacked with malformed JSON or size overflow | Strict parser, bounded allocation and adversarial corpus required before release |
| CLI or GUI differs from C99 semantics | One C99 evidence core; frontends may display but not recalculate receipt logic |
| Chain timestamp or attribution is falsified | Neither exists in minimal v1; chronology/authorship are not authenticated |

## Operational requirements later

- Document whether the engine witnesses deletion by modifying caller-owned buffers or by receiving explicit before/removed/after streams.
- Require explicit authorization for any filesystem mutation; avoid silently modifying user data.
- Use sanitized errors and opt-in diagnostics that never include deleted plaintext.
- Validate C FFI ownership, lifetimes and platform ABI handling.
- Review optional keyed commitments and signature/anchor schemes as separate protocol versions.
