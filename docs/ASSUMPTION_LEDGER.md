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
| A05 | Canonical JSON/receipt parser and chain | Phase 14 actual-source numeric/field-mask ACSL targets and bounded parser/chain negative evidence (exact-head verification required) | Full unbounded production C99 encoder/parser/chain, hash-domain and no-write-on-error WP/refinement proofs remain open |
| A06 | Rust FFI, CLI, TUI, GTK | Runtime and integration tests, not formal proof | Ownership, bounds, ABI layout and error refinement proofs |
| A07 | C source-to-executable compiler/linker semantics | GCC/Clang/ARM64 testing, not proof | CompCert or target-specific translation validation |
| A08 | OS, firmware and physical hardware | Model and executed target tests only | Explicit target-specific model and trusted hardware assumptions |
| A09 | Historical deletion, time, author and secure erasure | **Never claimed** | Independent witness, trusted head, signature and separate storage-erasure evidence |

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
