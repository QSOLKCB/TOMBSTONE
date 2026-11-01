# TOMBSTONE roadmap

**Phases 0–10 are merged. v0.1.0 is an immutable source release. Phase 11 is an open development PR with executed Frama-C/WP verification of the actual public C99 wrapper and both private hash-staging helpers: 18/18, 23/23, and 47/47 goals discharged. Independent exact-head review remains required before merging. The external SHA-256 provider contract is an assumption, not a verified cryptographic implementation.**

| Phase | Deliverable | Gate | Status |
| --- | --- | --- | --- |
| 0 — Foundation | Human/machine contract and fixtures | Documentation checks | Merged |
| 1 — C99 SHA-256 | OpenSSL EVP, binary-safe C ABI | Vectors, ASan/UBSan, reproducibility | Merged |
| 2 — C99 splice | Exact witnessed byte deletion and observed transition | Adversarial inputs | Merged |
| 3 — Canonical receipts | Strict v1 JSON and SHA-256 hash chain | Golden/invalid cases | Merged |
| 4 — Rust CLI | Safe C99 FFI, deterministic headless commands | CLI parity and sanitized I/O | Merged |
| 5 — Rust TUI | ncurses inspection, optional create-new save | PTY tests and C99 parity | Merged |
| 6 — Optional GTK4 | Isolated desktop frontend over same FFI | Xvfb and independent builds | Merged |
| **7 — Hardening/release gate** | Bounded C99 fuzzing, compiler/arch replay and release evidence | CI and independently reviewed frozen source | Merged; v0.1.0 released |
| **8 — Direct C99 bounded verification** | CBMC on actual C99 splice and observation | Mandatory unwind checks, symbolic inputs ≤4 bytes | Merged |
| **9 — Unbounded splice relation proof** | Production C99 splice helper with ACSL contracts and loop invariants | Frama-C/WP: 35/35 executed; exact-head review | Merged |
| **10 — Public witness validation proof** | Actual C99 prehash argument/length/mismatch decision helper; synthetic SHA failure tests | Frama-C/WP 25/25, exact-head review | Merged |
| **11 — Whole-wrapper modular proof** | Actual public `tb_witness_delete` plus `fingerprints` helper under external SHA-256 contract | Separate Frama-C/WP checks of each source function; all nonzero goals, RTE and original CI | Three production-source WP targets proved 88/88; exact-head review and merge pending |
| **Later proof expansion** | Real SHA-256/OpenSSL provider, ABI/compiled code, receipt chain, VST/CompCert | Separate complete proofs and explicit assumptions | Planned |

## Phase 11 — Whole-wrapper modular source proof attempt

- Development source refactors the existing local evidence construction into a private production `witness_stage` helper, preserving the public C ABI and API semantics. A verification-only translation unit includes the actual development `src/core/deletion.c` and adds ACSL contracts to the real `fingerprints` and `witness_stage` helpers.
- Three **separate** Frama-C/WP targets were successfully executed: `fingerprints` 18/18, `witness_stage` 23/23, and `tb_witness_delete` 47/47 at [run 41314458282](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41314458282). Phase 9's splice relation and Phase 10's prehash status checker remain required independent proofs.
- The external `tb_sha256_bytes` contract is **assumed**; it is not an OpenSSL or SHA-256 proof. No successful whole-wrapper claim is made until both Phase 11 proof logs discharge 100% of nonzero goals, with RTE obligations enabled.
- Preserved negative evidence: the original full-wrapper run 41307132302 proved 35/64 with 29 timeouts; Phase 11 run 41312320907 proved `fingerprints` 18/18 but the wrapper only 49/61 (12 timeouts); staging runs 41312928221 and 41314042829 were incomplete. After the live production refactor, run 41314458282 passed all three proof targets. Timeout, unproved memory-framing or a missing solver report is a hard stop.
- Preserve the published v0.1.0 tag, source archive, ABI, input-retention policy, receipt format and original test vectors.

## Phase 10 scope and proof boundaries

- The production `tb_witness_delete` invokes `witness_header_status`, which directly implements the public API's prehash argument/length/mismatch precedence without reading caller bytes. Frama-C/WP targets that exact source helper for *all* `size_t` inputs, with a no-write contract.
- A separate, proof-only translation unit includes the full original `src/core/deletion.c` and specifies a modular abstract SHA failure/no-write contract; **its whole-wrapper proof remains experimental and incomplete** (initial run 35/64 goals, 29 timeouts).
- The current unbounded proof gate covers prehash status precedence and nonmutation. The complete wrapper's success metadata and output preservation across all provider outcomes still require the planned whole-wrapper WP proof. Runtime synthetic-hash tests exercise those behaviors without claiming universality.
- An independent C99 failure-injection test invokes the actual wrapper against synthetic provider errors at all three SHA-256 calls; it verifies output immutability and early argument/length/mismatch errors.
- The new WP CI checks the proof log and rejects missing/zero/incomplete goals. **Only executed 100% goal discharge counts as a formal proof result.** No claim of verified OpenSSL, bytecode, Rust FFI, historical edits or universal hardware.

## Phase 9 scope and limits

- The actual `src/core/deletion.c` `tb_witness_delete` uses the new `splice_equal` helper; the mathematical contract is attached to that same production helper, not a second implementation.
- Frama-C/WP and Alt-Ergo attempt proof for arbitrary valid C `size_t` lengths: exact removed span and resulting after-buffer equality, 0/1 result equivalence, bounded loop indexing, and `assigns \\nothing` with strict, explicit readable-buffer preconditions.
- CI checks original C99 fixtures and the unchanged `v0.1.0` source release, and refuses to mark WP successful unless **all nonzero generated goals are proved**. Full solver logs are retained as artifacts.
- **Not yet proved:** the complete public `tb_witness_delete` wrapper including hash errors and all failure cases, entire JSON receipt engine, OpenSSL, Rust, executable semantics or alien hardware. See [formal verification](docs/FORMAL_VERIFICATION.md).

## Prior Phase 7 scope

- Clang libFuzzer targets for the bounded C99 receipt parser and exact-splice/transition APIs, instrumented with AddressSanitizer and UndefinedBehaviorSanitizer, with reproducible synthetic seed corpus.
- GCC and Clang compilation of the authoritative C99 backend in **independent Rust CLI builds**. Python's standard-library oracle verifies the fixed v1 schema hashes and byte-for-byte canonical JSON results without introducing a production duplicate.
- Linux x86-64 and ARM64 runner matrix for independently executed cross-compiler receipt replay, historical fixture continuity and malformed/chain negative tests.
- New [release gate](docs/RELEASE_GATE.md), [portability limits](docs/PORTABILITY.md) and [anchoring/privacy boundary](docs/ANCHORING_PRIVACY.md). No changes to existing receipt schema, output hashes, CLI or GUI contract.
- The exact PR head must receive review and green checks; the maintainer may tag a selected version **after merge** with evidence and asset checksums. No premature stable-release or secure-erasure claims.

The next action after this PR is review, any corrections, locally executed evidence where useful, and an independent **release decision**. A green CI status alone is not a release.
