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
| Unbounded C99 functional correctness and no UB | ACSL/Frama-C/WP | Not proved |
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
