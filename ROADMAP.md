# TOMBSTONE roadmap

**Phases 0–8 are merged. v0.1.0 is an immutable source release. Phase 9 is a development PR targeting Frama-C/WP proofs on the actual C99 splice relation; its outcome is gated on executed proof logs and exact-head review.**

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
| **9 — Unbounded splice relation proof** | Production C99 splice helper with ACSL contracts and loop invariants | Frama-C/WP: all goals proved; no vacuous passes, C99 regressions, exact-head review | In PR; not merged |
| **Later proof expansion** | Wrapper error paths, hash provider, ABI/compiled code, receipt chain, VST/CompCert | Separate complete proofs and explicit assumptions | Planned |

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
