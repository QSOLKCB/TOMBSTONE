# Phase 19 — Actual C99 receipt helper refinement

Context source: the **merged** private QSOL-FORMALISATION/1 `tombstone_phase19` route, revalidated against TOMBSTONE main at `8b4c87899c18524eb1ce3f6e89641504caff67cf`. This is a fresh implementation attempt; donor observations do not transfer proof status or Codex approval.

The production `src/encoding/receipt.c` Git blob is still `6fe3e8014e9c38ea42c43b9133f026967a4158e3`. Nothing changes `v0.1.0`, the C ABI or the three frozen receipt-v1 examples.

## Proof stages and boundaries

- **P19-01 — actual `equal32`:** `tools/phase19_equal32_overlay.py` derives a proof translation unit from the actual production C99 and Phase 18 ACSL. An explicit contract on the *external libc `memcmp`* models 32-byte equality and read-only inputs. The compiler and actual libc implementation are not proved. Frama-C/WP must discharge nonzero all-goal and RTE checks of the real `equal32` body; timeouts remain failures. This is not a proof of `memcmp` internals.
- **P19-02 — actual `calculate_hash`:** `tools/phase19_calculate_hash_overlay.py` inserts modular contracts for `good_receipt`, `format_json` and streaming SHA entrypoints; the latter use an explicit abstract private-state footprint. That is a **strong external-provider assumption** pending refinement against real OpenSSL/HACL state allocation, mutations, error statuses and cleanup. It does not prove the SHA algorithm, valid returned digest, full canonical formatter or hash-domain correctness. The actual C function is not replaced.
- **P19-03 — full chain refinement bridge:** Phase 18 already established 54/54 WP goals conditionally on `equal32` and `calculate_hash` contracts. Re-run those goals at the final new head and explicitly link independently discharged helper obligations. A green helper proof does not imply a proven provider or complete JSON engine.

Native `tests/formal/test_phase19_native.c` executes real production C99 helper logic with live OpenSSL and checks every possible single differing byte position (0–31), no mutation of its input buffers, a successful hash calculation and invalid-receipt early failure without writing its output. Finite tests do not constitute an unbounded theorem.

## Mandatory review and evidence

All proof overlays must strip to exactly the original C99 source with no substitute implementation. The Frama-C 32.1/Alt-Ergo pipeline uses `-wp-rte` and strictly fails on missing, incomplete, zero or timed-out goals. Preserve failed logs and source/assumption identities; do not repin stale historical evidence or re-label imported results as locally proved.

Evidence claims should distinguish:

- `EXECUTED_PROVED`: complete, nonzero current-head WP result under listed assumptions.
- `EXECUTED_INCOMPLETE`: failed/time-out/unknown WP result, retained unchanged.
- `NOT_RUN`: provider correctness, full JSON parser/formatter proof, source-to-binary correctness and physical/historical deletion unless separately verified.

Existing A04/A05 premises and issues #15–#18 remain open. Require current exact-head green CI and independent Codex review with no actionable defects before any owner-authorized merge. No automatic tag or release.
