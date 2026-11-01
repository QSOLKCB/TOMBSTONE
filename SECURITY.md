# Security and privacy model

**Scope today:** Phase 1 implements C99 SHA-256 through OpenSSL EVP. Phase 2 adds caller-supplied, exact byte-splice verification and observed-transition classification, returning only in-memory digests/lengths/offset. Neither library function opens files, deletes data, logs removed bytes nor serializes receipts. Phase 3 adds deterministic receipt serialization, strict parsing, and hash-chain checking; secure erasure, historic attestation, trusted anchoring infrastructure and authenticated historical deletion are not implemented. Phase 5 merged the Rust ncurses TUI; Phase 6 merged the optional GTK4 GUI. Phase 7 adds reproducible bounded C99 fuzzing, independent receipt replay and a pre-tag security/evidence gate, but no secure erasure or historical-authentication mechanism. Phase 4 provides a Rust CLI that reads explicitly named inputs or stdin, bounded at 64 MiB per input. Report security concerns via a private maintainer channel or GitHub's private vulnerability reporting where enabled; do not post real removed secrets in issues.

## Nonclaims

- A hash is **not encryption**, secure erasure, proof a file was actually erased, proof of who edited it, or proof of deletion time.
- Before/after hashes cannot identify which bytes were removed. Only witnessed-and-validated bytes justify an \`explicit-delete\` receipt.
- A hash of a predictable secret (PIN, short token, common phrase) can be brute-forced by guesses. A plain SHA-256 digest may disclose whether a guessed value was deleted.
- Receipt chains offer tamper evidence against changes *relative to an independently trusted hash head*. An attacker can rewrite an unanchored chain wholesale.
- Editors, swap, journals, storage snapshots, backups and caller memory may retain plaintext long after receipt creation.

## Phase 2 limitations

Witnessing verifies a mathematical splice identity, **not an externally authenticated edit event**. The caller supplies before/after/deleted bytes and an offset. Repeated bytes may make multiple offsets equally valid. The API never deduces deleted bytes from snapshots. Results are not confidential: SHA-256 of a short predictable secret can be guessed. Input pointers remain caller-owned and may still appear in swap, backups or editor history. Outputs and inputs must be disjoint; C99 cannot validate arbitrary caller pointer extents.

## Phase 3 tamper boundary

A self-hashed receipt or locally consistent chain is not an authenticated historical record: a malicious party can rewrite the whole chain. `tb_receipt_verify_chain` can compare the final digest with a caller-provided independently trusted head, but obtaining and safeguarding that trusted head is outside this library. The canonicalizer handles **only the fixed ASCII/JSON-safe integer receipt schema**, not arbitrary JSON. Receipts remain subject to dictionary guessing for short secret deleted spans.

## Phase 4 CLI and FFI boundary

The new Rust CLI loads caller-selected files/standard input into process memory, calls the C99 core through a minimal Rust FFI and emits *only* C99-derived canonical receipts or deterministic status JSON. The command does not delete or modify any input files and does not print their names/content in receipt output or diagnostics. Memory allocation is bounded by a 64 MiB per-input cap, but copies may remain in process memory, OS swap or external backups. The Rust adapter checks C ABI versions and bounds output buffers; the C ABI itself cannot validate arbitrary foreign pointers. Only trusted final hashes independently preserved outside the local history can anchor chain authenticity. The tool operates offline and has no telemetry, interactive prompts or network calls.

## Phase 5 interactive TUI boundary

The TUI prompts for selected paths; these are visible while typed but are not included in receipt JSON, reports or sanitized errors. Display text is filtered to printable ASCII to avoid embedded terminal-control sequences. All buffers are binary-safe and bounded (64 MiB per data file, 16 KiB per receipt), with at most 64 chained receipts. The UI can emit a canonical receipt only through an explicit save request that creates a **new** output file (Unix mode 0600), never overwriting an existing file. It does not delete input files or sanitize memory/swap. It requires an interactive terminal, and the core/headless CLI do not link ncurses. An entered predecessor digest is only a caller claim, not independently validated history.

## Phase 6 GTK4 desktop boundary

The desktop app uses system GTK4 only as an optional user interface, isolated from the headless Cargo workspace. File paths are visible while typed in GTK entries but are never included in canonical JSON, rendered receipt reports or application diagnostics. It reuses the Phase 5 C99-backed workflows for binary-safe inputs, restricted-size receipts, optional independently trusted chain heads and create-new-only saves. A failed or replaced evidence operation clears the last exportable receipt; nothing is automatically saved, edited or deleted. GTK4 may have its own runtime/display environmental behaviour; never treat its input fields as a secure secret-entry facility. There is no logging of deleted plaintext, telemetry, cloud access, signing or secure erasure.

## Phase 7 adversarial tests and anchoring boundary

The C99 parser and splice APIs now have sanitizer-backed libFuzzer targets seeded only with public synthetic fixtures. These check error-path immutability and canonical round trips, not actual deletion or privacy of guessed secrets. Independent Python SHA-256 replay only checks the *fixed* v1 ASCII receipt profile on real GCC/Clang C99-backed CLI builds. Neither fuzz coverage nor successful CI establishes formal correctness, cryptographic confidentiality or historical authenticity. See [anchoring/privacy](docs/ANCHORING_PRIVACY.md) and [release gate](docs/RELEASE_GATE.md).

## Planned controls

Use length-delimited buffers, overflow checks, strict schema/duplicate-key rejection, a cryptographic backend tested against known vectors, limited allocations, no logging of deleted bytes, no mandatory network connectivity, and meaningful error codes. Do not claim zeroisation is sufficient to erase all copies. The core never automatically deletes filesystem data without an explicit future interface, design review and tests.

An optional keyed commitment or external signature/anchor may be evaluated in later phases; neither is part of the current v1 proposal. See [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md).
