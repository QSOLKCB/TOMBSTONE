# Phase 19 — Actual C99 receipt helper refinement

Context source: the **merged** private QSOL-FORMALISATION/1 `tombstone_phase19` route, revalidated against TOMBSTONE main at `8b4c87899c18524eb1ce3f6e89641504caff67cf`. This is a fresh implementation attempt; donor observations do not transfer proof status or Codex approval.

The production `src/encoding/receipt.c` Git blob is still `6fe3e8014e9c38ea42c43b9133f026967a4158e3`. Nothing changes `v0.1.0`, the C ABI or the three frozen receipt-v1 examples.

## Proof stages and boundaries

- **P19-01 — actual `equal32`:** `tools/phase19_equal32_overlay.py` derives a proof translation unit from the actual production C99 and Phase 18 ACSL. An explicit proof-only `memcmp`-to-`phase19_memcmp` alias binds the unchanged body to a modeled 32-byte equality contract; this bypasses unsupported Frama-C libc allocation/danglingness predicates and **must not** be confused with proof of actual libc `memcmp`. The compiler and actual libc implementation are not proved. Frama-C/WP must discharge nonzero all-goal and RTE checks of the real `equal32` body; timeouts remain failures. This is not a proof of `memcmp` internals.
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

## Phase 18 bridge fidelity caution

The proof-only Phase 19 streaming SHA model has a private mutable state. Its actual `calculate_hash` proof target explicitly permits effects to that model state **in addition to the local 32-byte digest output**. Phase 18's original abstract `calculate_hash` specification permits only digest-output writes; these contracts are not syntactically identical. A passing Phase 19 hash proof therefore **does not by itself discharge Phase 18's stronger frame assumption**. A separately reviewed projection/heap-lifetime refinement is required to show that state changes are private to the provider and unobservable to callers. Do not report the P19-03 bridge as complete without it. Previous 37/46 attempts and their nine frame timeouts remain retained as negative evidence.

## Takeover verification and separate error-path attempt

The original 11/11 and 40/40 overlays and `phase19-helper-evidence-v1.json`
remain unchanged. Their evidence gate and twelve rejection tests now run in
the Phase 19 workflow. The WP log gate additionally requires the pinned
32.1 banner, exactly one RTE target, one scheduled-goal count and one complete
summary with the expected count. It rejects wrong targets, changed counts,
duplicated reports, unsupported predicates and solver failures. This is a
coverage check, not authentication of the execution or a provider proof.

`tools/phase19_hash_errors_overlay.py` is a **separate** proof attempt on
the same actual C body. It admits `TB_ERR_LENGTH` from streaming update:
the real provider has this public status, which the original unconstrained
context model omitted. It assumes the documented final-call no-write-on-error
guarantee and asks WP to prove that `calculate_hash` preserves all 32 output
bytes on every non-OK return. The old receipt is not evidence for this new
postcondition. [Run 41349751316](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41349751316)
discharged **41/41** goals at head `1f664a610f1f114c7eaeb4804c9c659090921d3a`
with `-wp-rte` under those external premises. The original private-state frame is retained;
there is no new provider, allocation-lifetime or P19-03 theorem.

`tests/formal/test_phase19_faults.c` executes 13 cases with the real helper:
frozen-fixture digest success, invalid receipt, formatter failure, allocation
failure, both streaming update failures (including length/state errors), and
final failure. Linker wrappers inject errors in this test executable only;
positive calls use real OpenSSL. It checks unchanged receipt/output bytes on
errors, exact call order, no later hash stage after failure, and exactly one
free of the acquired context. These are finite cleanup observations.

Disposable native mutants must fail a test assertion after successful
compilation: always-equal comparison, missing cleanup, output writes on error,
and swallowed errors. An always-true `equal32` proof mutant must also leave
an equality postcondition unproved under the **same** contracts; syntax errors
or missing reports do not count as semantic negative evidence. Original mutant
and positive solver logs are uploaded separately. Never copy these mutants
into production or use them as source identity baselines.

That first run proved the positive equality target (11/11) and left the
mutant's equality postcondition unproved (11/12, expected timeout), but its
negative-control checker expected an older log format and failed. The corrected
checker has tests for the actual 32.1 format and must pass a fresh CI run.
This failed workflow is **not** recorded as green. The unchanged Phase 18
chain independently reran at 54/54 in run 41349751507.

Original decoded GitHub job logs, including the earlier 13/17 and 37/46
failures, are retained under `formal/evidence/phase19/`. Their hashes, exact
head/checkout identities, conditional results and failure classifications are
in `machine/formal/phase19-error-path-attempt-v1.json`. This is an observation
record for that attempt, not current-head review approval. The local sanitizer
attempt could not complete because LeakSanitizer could not inspect `/proc` in
the execution environment; sanitizer coverage comes from the separate CI jobs.

The PR remains draft while the stronger Phase 18 bridge and exact-head
independent review are outstanding. A successful rerun of the unchanged
54-goal Phase 18 workflow still assumes its original helper frame.
