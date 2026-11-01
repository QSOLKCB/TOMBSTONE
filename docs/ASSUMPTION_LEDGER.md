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
| A04 | SHA-256 computation and actual OpenSSL EVP internals | NIST tests, not formally proved | Adopt and integrate a separately verified SHA-256, or provide machine-checked proof of selected implementation |
| A05 | Canonical JSON/receipt parser and chain | Golden vectors, negative tests and independent replay | Direct C99 parser, encoder and hash-chain WP proofs |
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
