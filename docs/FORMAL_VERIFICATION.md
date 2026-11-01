# TOMBSTONE Phase 8 — Formal proof obligations

**Status: verification proposal, not an end-to-end C99 proof.** Published v0.1.0 and its immutable tag are unchanged.

## Direct C99 contract

For valid disjoint, readable input buffers and a writable non-aliased output object, `tb_witness_delete` is required to return `TB_OK` exactly when the supplied byte buffers satisfy

    before = prefix ++ removed ++ suffix
    after  = prefix ++ suffix
    length(prefix) = offset
    length(removed) > 0

with status-specific invalid-input errors, exact lengths/offset on success, and **unchanged output on failure**. The function proves no historical deletion. `tb_observe_transition` must classify actual byte equality and never invent removed bytes. Invalid raw pointers remain outside the contract even when numerical lengths appear valid.

## Evidence and claim ledger

| Target | Instrument | Proof status |
| --- | --- | --- |
| Mathematical identities | Rocq, Lean, Isabelle/HOL | Planned — no theorem-checked result yet |
| Actual C99 splice/observation paths for 0–4-byte inputs | CBMC on unmodified `src/core/deletion.c` | New CI obligation; check exact-head logs before claiming PASS |
| Unbounded production splice equality helper (`splice_equal`), with valid-buffer premises | ACSL/Frama-C/WP | **35/35 WP goals discharged on [executed CI run 41305390928](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41305390928) at source blob `ed0a2107…`; the final PR head requires its own CI rerun** |
| Public `tb_witness_delete` wrapper, modular SHA boundary | Frama-C/WP + native injected failures | Phase 10: pure production prehash validation helper is the current unbounded WP target; the full wrapper is not proved |
| OpenSSL SHA algorithm/provider, including failures | Separate provider verification | **Assumed**, not proved by wrapper contract |
| All C99 memory/crypto/receipt operations | Frama-C/WP plus dependent proof | Not proved |
| Direct C99 source-to-machine refinement | Rocq/VST + CompCert | Not proved |
| Production SHA-256/OpenSSL EVP | Verified hash primitive or explicit external contract | Not proved here |
| Rust FFI, CLI, filesystem and GTK/ncurses | Dedicated ownership and OS contracts | Not formally proved |
| Arbitrary alien hardware | Target-specific verified model | Not universally provable without assumptions |

The CBMC harness `formal/cbmc/splice_harness.c` **includes the actual C99 implementation** rather than translating it. An independent, indexed byte oracle checks the splice status and metadata. Nondeterministic input bytes, lengths and offsets cover a *bounded* domain of up to four bytes. It separately checks that failed witnesses leave the output byte-for-byte unchanged and that observed transitions never become deletion claims.

**Important limitation:** The harness replaces the external `tb_sha256_bytes` call with a synthetic success-only function writing a fixed digest. Therefore these obligations concern splice/control-flow correctness *conditional on successful hashing*. They do not establish SHA-256 correctness, real OpenSSL error behaviour, secure erasure or complete cryptographic correctness. This stub must never enter the production build.

## What “universal” can mean

An unbounded proof can quantify over **all permitted inputs and all defined executions under specified assumptions**. CompCert's verified compilation can connect supported C semantics to supported machine semantics, but compiler front-end, assembler/linker, external libraries, runtime, hardware and physical faults require additional treatment. An alien terminal with 9-bit bytes, a novel ABI or unreliable memory is not covered without a model of that platform.

The strongest honest result is conditional: *if the implementation, compiler, dependencies and machine satisfy the verified contracts, the program satisfies the specified property.*

## Next proof milestones

1. Prove ACSL contracts against actual C99 using Frama-C/WP, including memory validity, overflow and all failed-output behaviours.
2. Prove independently checked Rocq/Lean/HOL splice and receipt algebra; verify **refinement** back to C, not merely similar-looking definitions.
3. Use VST and a supported CompCert verified compilation path for source-to-machine preservation.
4. GNAT/SPARK: verify a reference implementation and explicitly prove its correspondence to C99. Proving Ada alone is not proof of the C99 source.
5. Separate the SHA-256 provider, canonical receipt parser/encoder, hash-chain and Rust FFI into distinct contracts, each with its own proof receipts.
6. Record exact source SHA, prover versions, assumptions and executed goals. No fake “formally verified” badge until the relevant obligations are actually discharged.

See `formal/README.md`. The existing fuzzing, reproducibility, release assets, original C99 engine and `v0.1.0` tag remain unchanged.

## Phase 9 — Actual production C99 relation under ACSL/WP

The live `tb_witness_delete` code calls a private `splice_equal` implemented in the *same* `src/core/deletion.c`. Its ACSL contract states that, for nonempty removed bytes, valid readable buffers, valid lengths, and a caller-supplied offset, it returns true **if and only if** the supplied buffers satisfy the exact deletion-splice identity. A quantified postcondition covers *all* byte positions, not a bounded four-byte model. Two loop invariants preserve the checked prefixes and bound all indices; loop variants require termination. The `assigns \nothing` contract forbids any caller-visible writes.

The proof target is only the private helper. Frama-C/WP proofs on this helper do not imply that the public wrapper's error handling, output-write conditions, OpenSSL SHA-256 provider, receipt parser or compiled binary are proved. In particular the wrapper still requires separate contracts for the hash API, its fail-no-write guarantee, and the relationship between byte comparison and output status. Caller-supplied pointers must refer to genuine readable objects; invalid pointers and environmental faults are not proved away.

**Executed verification:** Frama-C 32.1 (Germanium), Qed 20 goals, Alt-Ergo 2.5.4 13 goals, one termination and one reachability goal. [Job log from run 41305390928](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41305390928) records `Proved goals: 35 / 35` for production-source `splice_equal`, with `-wp-rte` enabled. This does not constitute proof of the public wrapper. The final PR head must repeat these checks.

**Executed-gate commands:** `frama-c -wp -wp-fct splice_equal -wp-rte -wp-prover alt-ergo -cpp-extra-args="-Iinclude" src/core/deletion.c`, then `tools/check_wp_proofs.py` rejects zero goals or any unproved goal. Use the exact PR head's `formal-wp.yml` Actions run for the result. An ACSL annotation alone is never evidence of a completed theorem.

**Compatibility:** the released `v0.1.0` tag remains untouched; no production receipt ABI, JSON wire format, or test vectors are modified. Any future release needs its own exact-head review and reproducible packaging gate.

## Phase 10 — Prehash status proof and whole-wrapper proof boundary

The proof-only file `formal/framac/witness_wrapper.c` includes the real C99 `src/core/deletion.c`. It declares ACSL contracts on the public `tb_witness_delete` function and on the external `tb_sha256_bytes` **assumption**. The production headers, C99 source, Rust interfaces and immutable `v0.1.0` tag are not modified by this stage.

The currently executable WP target is the **production** `witness_header_status` helper, which proves the argument/length/mismatch prehash classification and `assigns \\nothing` across arbitrary `size_t` values. The experimental full-wrapper contract includes successful metadata and unchanged caller output, but its initial attempt proved 35 of 64 obligations and left 29 timeouts; therefore the public wrapper remains **formally unproved**. The abstract hash contract permits successful hashing or memory/crypto errors and requires digest output unchanged on failure. This contract is an **axiomatic external assumption**, not proof of the actual OpenSSL EVP function. Separate adversarial C99 tests deliberately fail the first, second and third hash calls and check that the original public output remains untouched.

Frama-C/WP with `-wp-rte` must discharge **all nonzero goals** before any formal claim is made; native tests and bounded CBMC cannot substitute for an unbounded WP result. The full SHA provider, binary compilation, runtime, author authenticity and real-world deletion are still unverified boundaries. See [Phase 10 contract and assumptions](PHASE10_WRAPPER.md).

**Exploratory whole-wrapper WP negative evidence:** [run 41307132302](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41307132302) reported `Proved goals: 35 / 64` and 29 timed-out obligations. This is intentionally recorded as *incomplete*, not a proven full-wrapper theorem. The separately required Phase 10 CI checks the simpler production prehash helper under the same strictly fail-closed all-goals gate.

**Strengthened Phase 10 prehash proof evidence:** [run 41308568840](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41308568840) discharged 25/25 WP goals (Qed 19, Alt-Ergo 2.5.4 6) on production C99 source blob `7f2e80d8f2d453d2c1b91ebebe323620c4ae5255`; the added goal establishes the reverse length-error implication. Native SHA failure-injection and the fail-closed proof log tests passed. This is a proof of the numeric prehash helper under the specified C model, not a whole-wrapper or SHA-256 proof.

## Phase 11 — Whole-wrapper modular proof attempt

The *actual* `src/core/deletion.c` is included by `formal/framac/witness_wrapper_v11.c`, which adds an ACSL contract for the existing `fingerprints` helper and specifies the public `tb_witness_delete` API. The independent Phase 9 and Phase 10 source proof gates stay enabled. Phase 11 deliberately uses two Frama-C/WP jobs, requiring complete nonzero goals for both `fingerprints` and `tb_witness_delete` rather than treating a helper contract as self-validating. See [Phase 11 obligations](PHASE11_WRAPPER.md).

**Unproved pending CI:** the complete public wrapper. The external `tb_sha256_bytes` contract is an assumption concerning input validity, 32-byte writes and fail-no-write behaviour. Actual OpenSSL SHA-256, backend state and cryptographic digest correctness remain outside scope. The prior 35/64 result is preserved as negative evidence.
