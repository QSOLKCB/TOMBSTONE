# TOMBSTONE — Assumptions and closure ledger

Theorems have **premises**; running multiple theorem provers cannot remove
the need for a C memory model, trusted source/ABI translation or reliable
hardware. TOMBSTONE closes software obligations incrementally, with exact
source identities, evidence and separately documented residual assumptions.

| ID | Boundary | Established evidence | Next technical closure |
| --- | --- | --- | --- |
| A01 | Actual C99 witnessed byte splice | Phase 9 ACSL/WP | Retain exact-source and input-validity gates |
| A02 | C99 witness prehash status and whole wrapper | Phase 10 and Phase 11 ACSL/WP, conditional on SHA provider | Verify actual SHA wrapper rather than assume it |
| A03 | C99 `tb_sha256_bytes` error/status/output/resource handling | Phase 12 injected failures against real C99 source and actual EVP on success — **executed tests, not full formal proof** | Source-level WP contracts for C99 wrapper under explicit EVP/allocator model |
| A04 | SHA-256 computation and actual OpenSSL EVP internals | OpenSSL NIST vectors; Phase 13 opt-in pinned HACL* extracted-C candidate (upstream F* verification), **not proof of OpenSSL or adapter** | Reproduce F* proof on exact upstream revision; C adapter/ABI refinement and source-to-binary translation |
| A05 | Canonical JSON/receipt parser and chain | Phase 14 modular ACSL/CBMC, Phase 17 prehash CBMC, and **Phase 18 actual unbounded 54/54 chain WP under explicit equal32/calculate_hash contracts** | Prove real helper/provider refinement, full parser/encoder and hash-domain/error semantics before closing A05 |
| A06 | Rust FFI, CLI, TUI, GTK | Phase 15 direct C99/Rust ABI layout/discriminant and error/no-write tests on specific Linux targets (execution gate pending) | Unbounded ownership, pointer/aliasing, panics and ABI refinement proofs |
| A07 | C source-to-executable compiler/linker semantics | Phase 15 independent repeat-build executable hashing and exact target/source/toolchain receipts (executed evidence only when CI passes) | CompCert or target-specific translation validation for actual binary and external calls |
| A08 | OS, firmware and physical hardware | Phase 16 C99 Linux 8-bit/little-endian/64-bit target probe and offline trust ledger; tests are not hardware proofs | Independently attested OS, firmware, memory and actual hardware fault model |
| A09 | Historical deletion, time, author and secure erasure | Phase 16 strict offline externally supplied head comparison; does not establish head custody, identity, timing or an event | Independently retained head, witness/identity/time provenance, and device-specific forensic erasure evidence |

## Phase 12 — Executed C99/OpenSSL boundary fault evidence

The `tests/formal/test_provider_faults.c` harness links TOMBSTONE's **actual
unchanged** `src/crypto/fingerprint.c` with actual `libcrypto`. Only external
function return values are injected through linker `--wrap` at `calloc`,
`EVP_MD_CTX_new`, `EVP_DigestInit_ex`, `EVP_DigestUpdate` and
`EVP_DigestFinal_ex` (including an incorrect digest length).

The test checks status mapping, unchanged caller output on errors, context
cleanup on the exercised paths, invalid pointer/length rejections before
allocations, correct real EVP SHA-256 for the known-answer success input,
zero-length input and streaming failure-state transitions. Both GCC and
Clang independently compile and execute the evidence in CI. No fake EVP
implementation is linked into production.

**What this does NOT prove:** that actual OpenSSL always satisfies the
Phase 11 assumed ACSL contract, that SHA-256 outputs are correct for all
possible messages, or that memory/OS/compiler behaviour is universally safe.
Phase 12 is an adversarial *execution* milestone; mathematically closing the
external digest contract requires a verified implementation or further proof.

The `v0.1.0` source release is immutable, and proof claims never transfer to
new source blobs without new evidence. No merge without exact-head review.

## Phase 13 candidate — formally verified SHA-256, not an assumed EVP

HACL* / EverCrypt is a candidate: its [upstream project](https://github.com/hacl-star/hacl-star)
documents F*-verified SHA-2 primitives extracted to portable C, and its
[verified algorithm matrix](https://hacl-star.github.io/Supported.html)
includes SHA2-256. Upstream documentation is evidence about **their specified
implementation and verification**, not automatically about TOMBSTONE's use.

Before integrating, require a specific immutable upstream commit/release, its
F*/Low* proof origin and generated-C source identity; verify that the
distribution/license and required dependencies are suitable; retain a
reproducible build and audit the exact C ABI and input-length/byte-order
conventions. Independently compare OpenSSL and HACL* against NIST vectors,
binary inputs, streaming/chunk-boundary equivalence and historical receipt
fixtures. Only then attempt a separate Frama-C/CBMC/ABI refinement proof
connecting **the exact compiled provider used** to the Phase 11 hash contract.

No SHA provider replacement, OpenSSL removal, source release modification or
algorithmically-verified claim is made by Phase 12. HACL* proof assumptions,
generated-code translation, the compiler and the hardware must be included
in the resulting trust ledger.

## Phase 13 — Pinned candidate and exact residual trust boundary

The optional HACL* implementation in [Phase 13](PHASE13_HACL.md) is pinned to
`f557259007db9933442dde10aa995c1b00bd3446`. An offline test compares
**all 16 copied upstream Git blob identities**, including KaRaMeL compatibility
and endian headers, to hashes recorded from that immutable upstream tree.
The unmodified generated implementation is MIT-licensed. No part of the
existing OpenSSL `src/crypto/fingerprint.c` is replaced or claimed verified.

The HACL adapter is new and independent from the upstream proof: it owns
allocation, pointer/length conversion, chunking, state transitions, the public
ABI and no-write-on-failure discipline. The test-only linker injection plus
GCC/Clang receipt parity are *executed evidence only when the exact-head CI
jobs pass*, not a proof of these properties for all permitted inputs.
Executed Phase 13 [run 41321354704](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41321354704) used CBMC 6.11.0 to check 584/584 bounded properties on the **actual adapter source** under a synthetic HACL boundary. The verified conditions are bounded status, failure-no-write and state transitions, NOT SHA-256 algorithmic correctness. The exact two proof-source blobs and conditions are in `machine/formal/phase13-adapter-cbmc-v1.json`, with an offline identity gate. The upstream F* proof and KaRaMeL extraction have **not** been independently rerun at the exact revision. The unbounded Frama-C/real-provider/ABI refinement and compiler evidence are still open.
The published `v0.1.0` SHA-256 baseline is immutable.

### Phase 13 executed checks and residual proof boundary

At [run 41321354704](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41321354704), all four x86-64/ARM64 GCC/Clang HACL/OpenSSL parity jobs and direct-source CBMC adapter checks passed. CBMC verified 0/195, 0/195, and 0/194 failed properties for bounded one-shot, streaming and invalid-input harnesses under a synthetic, explicitly **modeled** HACL provider. Real upstream SHA-256 and the adapter's unbounded correctness were **not formally proved by these local checks**. See `machine/formal/phase13-hacl-evidence-v1.json` and the source-pinning check.

## Phase 14 — Actual receipt engine, bounded and modular evidence

The [Phase 14 scope](PHASE14_RECEIPTS.md) applies to production
`src/encoding/receipt.c`; no v1 wire-format or digest change is authorized.
The WP targets are the **actual** `decimal_step` overflow check called by
`number`, and the actual `unseen_field` bitmask predicate called by both
nested and top-level field parsers. Their contracts are scoped to those
functions, not to all possible JSON inputs or the complete `tb_receipt_parse`
implementation. The direct-source CBMC checks use bounded symbolic input;
the runtime tests use the real C99 hash provider and fixture set. All three
historical JSON blobs and the proof inputs are pinned offline.

There is no theorem yet connecting arbitrary parsed input to canonical body
bytes, domain-separated SHA-256, complete chain linking, or public error
output immutability over all permitted inputs. A local internally consistent
chain lacks any independent trusted head, time, author or deletion history.
**A05 remains open** until full-source proofs are actually discharged and
reviewed; Phase 13's outstanding SHA/ABI/translator premises still apply.

## Phase 15 — FFI layouts and target-specific binary evidence

The [Phase 15 scope](PHASE15_ABI.md) performs actual C99 layout observations
and compares them to the private Rust `repr(C)` structures, tests native
status/no-write paths and the CLI 64 MiB boundary, and records two isolated
release build hashes on the same Linux compiler/backend/architecture tuple.
It does **not** independently establish compiler correctness, FFI lifetime
soundness, target linker/OS behaviour or machine-code refinement. Failure
of any individual ABI or executable identity test blocks the evidence claim,
not grounds to relax safety checks. C99 remains authoritative and the
immutable `v0.1.0` baseline stays untouched. A06/A07 remain conditional.

## Phase 16 — Conditional target model and externally witnessed events

The [Phase 16 trust boundary](PHASE16_TARGET_TRUST.md) is machine-readable in
`machine/phase16/trust-boundaries-v1.json` with enforced A01–A09 categories,
exact pre-existing source Git blobs and preserved `v0.1.0` identity. C99
platform probes on GCC/Clang Linux x86-64 and AArch64 reject unsupported
integer/endianness/ABI models; this is not a hardware or verified compiler
attestation. The Rust CLI can optionally consume a strict, independently
retained chain head from an offline regular file, then invoke **unchanged
C99 chain verification**. No head is automatically generated, stored,
signed or silently accepted by the CLI.

A matching head establishes only equality to the *caller supplied* value.
Independent custody, authenticated identity, trusted chronology, storage
controller behavior and physical erasure cannot be derived from receipts.
The machine contract rejects upgrading A08/A09 into proved code claims and
separates verified splice relations from observed filesystem events and
storage-erasure evidence. The live SHA provider and incomplete canonical
receipt/FFI/source-to-binary proofs remain conditional (issues #15–#17).

## Phase 17 — Actual chain verifier early rejection and frozen-fixture replay

[Phase 17](PHASE17_CHAIN.md) targets the actual C99
`tb_receipt_verify_chain`, preserving the exact Phase 14/16 production
source blob and pinned original three receipt-v1 fixtures.
The direct-source CBMC targets cover argument/count and invalid-genesis
**prehash** rejection only; the complete verifier's digest-success and
error-status propagation are outside those bounded proof goals.
The native test exhaustively reorders the three frozen records,
probes prefix/trusted-head consistency, tampers with each digest/link
and uses a new valid genesis to prove that a locally consistent chain
can still fail against an earlier independently supplied head.
Even a green 8-target CI run would not prove universal SHA,
canonicalization, source-to-machine semantics or external head custody.
**A05 stays open** (issue #16); this milestone is an incremental proof
gate, not proof completion.

## Phase 18 — Unbounded actual C99 chain loop under assumed SHA contracts

The [Phase 18 proof scope](PHASE18_CHAIN_WP.md) uses an ACSL-only generated overlay of the unchanged real src/encoding/receipt.c; the original source blob remains identical. [Executed run 41334542042](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41334542042) discharged **54/54** nonvacuous Frama-C/WP goals with -wp-rte, arbitrary valid nonempty counts, successful-path genesis, all predecessor links, caller no-write, and optional trusted-head byte equality.

This is conditional on **unproved external helper contracts**: equal32 must exactly compare 32 readable bytes without writes; calculate_hash must write only the local 32-byte output and return within the documented status set. Neither actual hash provider nor digest correctness, full JSON parser/encoder, external anchor custody, source-to-binary, hardware or real-world deletion is established. A05 remains open; the exact source, solver result and exclusions are captured in machine/formal/phase18-unbounded-wp-v1.json with fail-closed negative controls. A04/A06–A09 premises remain unchanged.

## Phase 19 — Actual helper refinement boundaries

The Phase 19 work ([scope](PHASE19_HELPERS.md), issue #28) tests the actual production `equal32` and `calculate_hash` functions without editing the pinned receipt source. The private `tombstone_phase19` donor is reference data, not current proof acceptance. Libc memcmp semantics are external; the proof-only streaming SHA abstract state is not the real provider's allocation, mutation, cleanup or algorithm proof. Any current-head partial/time-out formal result remains incomplete. A04/A05, JSON, source-to-binary, custody, chronology and erasure obligations remain open.

The separate error-path overlay admits streaming `TB_ERR_LENGTH` and adds an
output-preservation obligation under the provider's documented final-error
frame. The original 40-goal record cannot establish that stronger claim.
Native failure injection checks cleanup on 13 finite paths; it does not close
the universal heap-lifetime obligation. P19-03 remains blocked by the private
provider-state effect absent from the original Phase 18 frame.

The [P19-03 follow-up](PHASE19_BRIDGE.md) introduces a separately named
caller-memory composition with a shared helper/chain contract environment and
a linear ownership/call-protocol model. It preserves the original Phase 18
theorem. The new frame permits private provider effects, so it does not prove
the old literal global frame. Backend separation, allocation/deallocation,
`good_receipt`, `format_json` and real SHA remain explicit open premises.
Solver evidence and exact-head review are required before accepting this new scope.
