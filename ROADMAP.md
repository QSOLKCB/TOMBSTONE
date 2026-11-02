# TOMBSTONE roadmap

**Phases 0–18 are merged; v0.1.0 remains immutable. Phase 19 helper proofs merged in PR #27. P19-03 caller-memory composition merged in PR #29. Phase 20 targets actual receipt validation and formatter contracts; see docs/PHASE20_RECEIPT_PREREQUISITES.md. Source and provider assumptions remain explicit; actual WP evidence is required before declaring closure.**

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
| **11 — Whole-wrapper modular proof** | Actual public `tb_witness_delete`, `fingerprints` and `witness_stage` under assumed SHA provider contract | Frama-C/WP 18/18, 23/23, 47/47 (88/88), exact-head review | Merged |
| **12 — Actual SHA provider boundary** | Actual C99 SHA wrapper + real EVP with test-only failure injection, source identity ledger | GCC + Clang negative/positive outcomes, exact-head CI/review | Merged in PR #14 — executed failure evidence, no SHA theorem |
| **13 — Verified SHA digest primitive** | Pinned generated HACL* SHA2-256 as optional backend; existing API and receipt wire bytes | Immutable upstream identity, fault tests, GCC/Clang x86-64/ARM64, exact parity; separate adapter/refinement proof remains required | PR #19 merged; residual provider refinement tracked in #15 |
| **14 — Canonical receipts and chains** | Actual C99 decimal-overflow and duplicate-bit WP obligations, bounded parser model, encoder/chain adversarial replay | Nonzero complete WP/CBMC goals, GCC/Clang x86-64/ARM64, frozen v1 blob identities | PR #20 merged; full parser/chain proof still open in #16 |
| **15 — Rust and compiler refinement** | Measured C99/Rust ABI, error/output parity, 64 MiB caps and two isolated release builds | GCC/Clang x86-64/ARM64 × OpenSSL/HACL execution, identical binary receipts, independent exact-head review | PR #21 merged; full source-to-binary refinement still open in #17 |
| **16 — Platform and provenance closure** | Explicit C99 target model, externally supplied offline head file, source-linked proof/trust ledger and physical-event distinctions | Negative custody/claim-inflation tests, Linux GCC/Clang x86-64/ARM64, exact-head review | PR #22 merged; physical and identity/time claims remain external |
| **17 — Direct receipt-chain verification gates** | Real C99 prehash rejection, all six frozen-fixture chain permutations and trusted-head controls | CBMC exact-source 3 targets, GCC/Clang x86-64/ARM64 × both SHA providers | PR #24 merged; prehash proof is bounded |
| **18 — Unbounded receipt-chain WP** | Unchanged C99 verifier under explicitly assumed calculate_hash/equal32 contracts | Frama-C 32.1: 54/54 goals under RTE, unbounded invariants and source/frame gate; exact-head review | PR #26 merged; SHA/JSON/physical assumptions still open |
| **19 — Real helper refinement** | Prove actual equal32 and calculate_hash contracts; connect conditional chain result | Exact-source Frama-C/WP with RTE, real libc/SHA assumptions, native controls and review | PR #27 and #29 merged; conditional caller-memory composition; issue #28 remains open |


## Phase 20 — Receipt validator and formatter prerequisites

- Check actual `good_receipt` and `format_json`, their internal validators and both actual hex encoders, while preserving the shared Phase 19 composition contracts.
- Require exact-source WP with RTE, explicit libc format/string/frame premises, semantic controls, full execution evidence and fresh exact-head review. Canonical-byte meaning and actual streaming SHA-provider refinement remain separate obligations.
- See [Phase 20 scope](docs/PHASE20_RECEIPT_PREREQUISITES.md). Draft PR #30 retains the latest 158/182 formatter result and a reproduced contradiction in the pinned Bytes theory. Resolve the model inconsistency before trusting new proof results; then finish the formatter and its formal mutation controls, refresh evidence and obtain exact-head independent review. Historical counts are not proof acceptance.

## Phase 19 — Actual C99 helper refinement

- Load the selective private `tombstone_phase19` reference route and revalidate the current source; no donor result becomes accepted proof automatically.
- Target actual `equal32` under an explicit external `memcmp` contract; target actual `calculate_hash` under explicit formatter and streaming SHA provider contracts. All positive WP claims need executed complete goals.
- Preserve and re-run the original Phase 18 54/54 theorem independently; the [P19-03 caller-frame composition](docs/PHASE19_BRIDGE.md) uses a separately named private-state frame and explicit ownership premises, not silent weakening of the original theorem; actual SHA digest correctness, whole JSON engine, runtime/compiler and historical claims remain open. See [Phase 19](docs/PHASE19_HELPERS.md) and issue #28.

## Phase 18 — Conditional unbounded C99 receipt-chain proof

- Executed [Frama-C/WP run 41334542042](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41334542042) discharged **54/54** goals with RTE on the unchanged production C99 chain verifier for arbitrary valid nonempty chain counts. A generated ACSL overlay strips exactly back to the original source blob.
- On success, the modular theorem guarantees genesis, every predecessor's 32-byte equality, and optional trusted-head byte equality; it proves no caller-memory writes.
- **Assumed, not proved:** equal32 byte equivalence and calculate_hash status/output frame. Real SHA-256 digest correctness is neither assumed nor established. Full parser/encoder, crypto provider, machine code, OS and historical-event premises remain open. Evidence is preserved in machine/formal/phase18-unbounded-wp-v1.json. See [Phase 18 scope](docs/PHASE18_CHAIN_WP.md) and [issue #25](https://github.com/QSOLKCB/TOMBSTONE/issues/25).

## Phase 17 — Incremental A05 chain integrity

- Production `src/encoding/receipt.c` remains byte-identical to Phase 14 and 16. Direct-source CBMC verifies argument/null/oversized and invalid genesis pre-hash rejection without assuming real-provider success.
- Full production C99 replay checks all six frozen receipt orderings, correct and wrong trusted heads, prefixes, invalid predecessor states and digest tampering, across GCC/Clang Linux x86-64/ARM64 × OpenSSL/HACL.
- Source-provenance and negative-evidence checks fail closed on changed proof inputs; `v0.1.0` and historical fixtures remain untouched. Full A05/actual SHA provider proofs remain conditional. See [Phase 17](docs/PHASE17_CHAIN.md), [issue #23](https://github.com/QSOLKCB/TOMBSTONE/issues/23).

## Phase 16 — Target assumptions and independent evidence boundary

- A test-only C99 probe enforces the declared Linux 8-bit-byte, little-endian, 64-bit pointer/`size_t` ABI; the offline machine ledger pins all pre-existing C99 source blobs, frozen v1 receipts, released source reference and A01–A09 proof/test/trust classifications.
- Optional `verify-chain ... --trusted-head-file path` reads a strictly formatted, separately retained 32-byte SHA-256 commitment and delegates verification to the **unchanged C99** chain engine. It never creates a trusted anchor or silently trusts a chain-derived head.
- Adversarial regressions require locally consistent rewritten chains to fail against a separately supplied earlier head, and reject malformed heads, ambiguous options, symlinks and attempts to promote conditional evidence into hardware/identity/erasure claims.
- **Residual boundary:** external custody, identity, chronology, filesystem event sensing, physical storage erasure, compiler and firmware/hardware correctness remain unproved. No signer/key lifecycle is introduced. See [Phase 16 target-trust contract](docs/PHASE16_TARGET_TRUST.md) and issue #18.

## Phase 15 — Rust FFI ABI and target-specific build evidence

- Actual C99 header-derived sizes, alignments, offsets, enums and status discriminants are compared to the private `repr(C)` Rust FFI structs by a test-only oracle compiled on each target; no public ABI changes.
- Rust/C99 error paths check no mutation of caller fields/buffers for failed calls. CLI cap tests require exactly 64 MiB to work and 64 MiB + 1 to fail with no stdout or pathname leak.
- Each supported Linux x86-64/ARM64 GCC/Clang + OpenSSL/HACL configuration independently builds two Rust/C99 release executables, compares exact bytes, and stores a source/toolchain/target/binary SHA receipt. Negative controls reject missing/mismatched artifacts.
- This is **not** formally verified source-to-binary translation. Compiler, optimization, linker, OS/hardware, FFI provenance and real-provider semantics remain scoped premises. See [Phase 15](docs/PHASE15_ABI.md) and issue #17.

## Phase 14 — Production canonical receipts and hash-chain assumptions

- Actual `src/encoding/receipt.c` decimal accumulation and field uniqueness are independently specified in ACSL, then checked under Frama-C/WP with runtime-error obligations.
- A direct-inclusion CBMC harness checks bounded numeric parsing, string buffer and whitespace cursor safety; no synthetic complete JSON parser is substituted.
- Actual C99 encoding/parsing/chain tests exercise duplicate, escaped duplicate, unknown, malformed numeric, output-immutability, tamper, chain truncation and trusted-head negative controls under both OpenSSL and opt-in HACL*, on GCC/Clang x86-64/ARM64.
- An offline evidence gate rejects changed proof inputs or the three immutable v1 fixture files. **Open:** unbounded full parser, canonical serializer and complete hash-chain proofs; SHA provider, compiler and external trusted-head assumptions. See [Phase 14 scope](docs/PHASE14_RECEIPTS.md) and issue #16.

## Phase 13 — Pinned HACL* alternative, with explicit residual assumptions

- The original OpenSSL provider is still the default and unchanged. `SHA256_BACKEND=hacl` selects a separately built C99 backend; Rust uses `TOMBSTONE_SHA256_BACKEND=hacl`.
- Upstream HACL*/KaRaMeL C and header files are pinned byte-for-byte to Git commit `f557259007db9933442dde10aa995c1b00bd3446` with 16 expected Git blob hashes checked offline by `tools/check_hacl_source.py`.
- The C adapter handles streaming, state, allocation failure and caller-output immutability. The test-only linker-wrap harness injects allocation and HACL update failures. CI independently checks exact receipt bytes with GCC/Clang and x86-64/ARM64; completion requires exact-head results.
- **Executed:** bounded CBMC 6.11.0 checked 584/584 properties with synthetic HACL allocation/update/digest calls in [run 41321354704](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41321354704); source and model identities are pinned in `machine/formal/phase13-adapter-cbmc-v1.json`. **Still open:** actual F* verification replay at this revision, unbounded C adapter/ABI refinement against real HACL under Frama-C or CBMC, source-to-binary proof and execution on arbitrary hardware. Upstream proof claims are conditional, and do not prove OpenSSL, the new adapter or historical deletion. Do not close issue #15 or merge/tag before meeting its remaining acceptance gates.

See [Phase 13 details](docs/PHASE13_HACL.md).

## Phase 12 — Provider boundary under live OpenSSL

- Production `src/crypto/fingerprint.c` remains unchanged and is pinned by its Git blob SHA in `machine/formal/phase12-provider-boundary-v1.json`.
- The Linux/GNU linker `--wrap` harness compiles **that actual C99 file** and calls genuine OpenSSL EVP on positive paths while injecting failures at each external allocation/init/update/final boundary, including the incorrect digest-length case.
- It verifies observed return statuses, unchanged caller digest on errors, cleanup of contexts allocated on each reachable injected path, streaming failure-state handling and actual NIST digests. Executed successfully on **GCC and Clang** at [run 41316764004](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41316764004).
- This is *adversarial execution evidence*, not an unbounded proof of OpenSSL or SHA-256 correctness. Phase 13 must close the algorithm/provider assumption before making that claim.
- The ordered programme, explicit nonclaims and platform assumptions are in [docs/ASSUMPTION_LEDGER.md](docs/ASSUMPTION_LEDGER.md).

## Phase 11 — Whole-wrapper modular source proof (completed)

- Development source refactors the existing local evidence construction into a private production `witness_stage` helper, preserving the public C ABI and API semantics. A verification-only translation unit includes the actual development `src/core/deletion.c` and adds ACSL contracts to the real `fingerprints` and `witness_stage` helpers.
- Three **separate** Frama-C/WP targets were successfully executed: `fingerprints` 18/18, `witness_stage` 23/23, and `tb_witness_delete` 47/47 at [run 41314458282](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41314458282). Phase 9's splice relation and Phase 10's prehash status checker remain required independent proofs.
- The external `tb_sha256_bytes` contract is **assumed**; it is not an OpenSSL or SHA-256 proof. All three Phase 11 WP targets discharged nonzero goals; the assumption remains open for Phase 12/13.
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
