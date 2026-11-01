# Instructions for coding agents

Follow [ARCHITECTURE.md](ARCHITECTURE.md), [INVARIANTS.md](INVARIANTS.md) and [ROADMAP.md](ROADMAP.md) before editing.

## Project contract

- **C99 is authoritative:** put byte processing, hashing, canonical receipts and validation under \`src/\`, public ABI under \`include/tombstone/\`. Rust/GTK are interfaces, not alternative evidence engines.
- Keep **human-facing Markdown** in root and \`docs/\`; keep **machine-readable contracts, schemas, and receipts** in \`machine/\`. Do not mix machine JSON with narrative fields.
- Never claim a diff proves which bytes were removed. Only an actually witnessed and checked splice may produce \`explicit-delete\`.
- Never log, commit, export or store user deleted plaintext by default; public toy fixtures are explicitly exempt. Inspect [SECURITY.md](SECURITY.md) first.
- Preserve the repository's existing **Apache-2.0** license unless the maintainer explicitly requests a change. Avoid Node.js dependencies.
- Reject unknown versions and malformed/duplicate-key records. Never silently change historic evidence or recanonicalize it into a new version.
- Keep core offline and usable without GUI, network, cloud, telemetry or Rust at runtime.
- Treat interfaces as separate milestones: C99 library first, Rust adapter/CLI second, TUI third, optional GTK later.
- Tests must distinguish **executed**, **not executed**, **inferred** and **planned** claims. Do not fabricate CI outcomes.

## Review and evidence discipline

Review the **exact head SHA**; report only actionable correctness/security defects with minimal reproduction, expected vs actual results and whether executed or reasoned. Do not re-report fixed findings. Propose small PRs with tests and clear rollback. Do not merge merely because another PR passed review.

## C99 and Rust (Phase 5 TUI and optional Phase 6 GTK4) commands

\`make\` builds the native static archive. Requires OpenSSL development headers and pkg-config. C99 SHA-256 resides in `src/crypto/fingerprint.c`; verified splice and classification in `src/core/deletion.c`. Public headers additionally include `include/tombstone/receipt.h`; JSON encoding and parser live in `src/encoding/receipt.c`.

\`\`\`sh
make
make test
make sanitizer-test
make reproducibility
make docs-check
\`\`\`

**Implemented:** C99 one-shot/streamed SHA-256, exact-splice verification with required nonempty removed span and offset, and observed-change/no-op classification without deletion inference. Return only SHA-256, sizes and offset; failure leaves output untouched.

**Not implemented:** historical proof of editing or filesystem deletion. Phase 5 TUI is merged. Phase 6 optional GTK4 app is in PR pending review. Canonical v1 JSON and hash-link verification are implemented; a trusted head from outside the local chain remains required to detect wholesale rewriting. Never claim that before/after hashes prove removed bytes.

**Phase 4:** Rust `bindings/rust` is a safe FFI adapter and `apps/cli` is a noninteractive CLI. They MUST call the original C99 API and must not reimplement SHA-256, splice validation, receipt canonicalization, or chain verification. No external Rust crates are needed. Verify using:

```sh
cargo test --workspace --offline --locked
cargo build -p tombstone-cli --release --offline --locked
```

**Phase 5 TUI:** `apps/tui` is an ncurses frontend; it must only call `tombstone-ffi` for evidence semantics, never fork C99 hashing/receipt logic. It must require a terminal, sanitize echoed paths in diagnostics, reject automatic save/overwrite, and permit exporting only canonical JSON. Run `cargo test --workspace --offline --locked` with system `libncurses-dev`, plus `cargo build -p tombstone-tui --release --offline --locked`. Headless CLI CI must remain runnable without ncurses by testing its packages separately.

**Phase 6 GTK:** `apps/gtk/` has its own Cargo workspace and lockfile, excluded from root. Build only when selected with `cargo test --manifest-path apps/gtk/Cargo.toml --offline --locked`; require system libgtk-4-dev. GTK4 is UI-only, reuses the Phase 5 Rust workflow functions and must never duplicate C99 cryptography, log input paths/secret bytes, auto-save or overwrite receipts. Run desktop smoke test with Xvfb in CI. Root workspace tests and the CLI/TUI must remain GTK-independent. Review all native GTK callback safety carefully.

For CLI development enforce deterministic JSON on stdout, stderr-only errors, no implicit prompts, no logs of plaintext/paths, explicit exit statuses and 64 MiB file caps. A supplied `--previous` is not independent proof of a valid preceding receipt; `verify` checks one record, while `verify-chain` checks the whole chain. A trusted external anchor is always an explicit caller input.

Review the **exact head SHA** and distinguish executed tests from inferred results. Keep each future milestone narrow, evidence-gated and independently reviewable.

## Phase 7 release discipline

Run `make fuzz` (requires Clang/libFuzzer with sanitizers) and the GitHub Actions architecture/replay matrix. This adds only synthetic fuzz inputs: never include user secrets in corpora or failure artifacts. `tools/check_portability.py` is an **independent test oracle**, not a production canonicalization implementation. Do not silently alter existing v1 receipt hashes, C99 API, ABI or machine contracts.

Before any tag, enforce [docs/RELEASE_GATE.md](docs/RELEASE_GATE.md): preserve source, distinguish executed from inferred platform coverage, exact-head independent review with no actionable defects, collect CI evidence, source/asset checksums, and explicit maintainer decision. **Do not create a tag automatically or merge based on a prior-head approval.**

## Phase 9 proof discipline

The actual production C99 `splice_equal` function has quantified ACSL contracts and loop invariants. Run the native tests and `formal-wp.yml` with Frama-C/WP and Alt-Ergo, then inspect *executed* proof counts. `tools/check_wp_proofs.py` must reject missing, partial or vacuously zero proof goals; never suppress RTE or loop-related obligations merely to obtain a green check. Report assumptions including `\\valid_read` and the separate SHA provider contract. A successful relation-helper proof is **not** an unbounded end-to-end proof of `tb_witness_delete`, OpenSSL, receipt JSON, compiler, memory faults or a different architecture.

## Phase 10 modular proof boundaries

The public C99 wrapper's contracts are in `formal/framac/witness_wrapper.c`; the translation unit includes the **actual** `src/core/deletion.c`. The synthetic hash contract and native fault-injection stub are *verification-only*, not production. Run `formal-wrapper.yml`, require nonzero complete Frama-C/WP proof goals with `-wp-rte`, and distinguish hash-provider assumptions from proved obligations. A successful wrapper proof must not be advertised as verified OpenSSL, filesystem erasure or machine code. Retain the exact-head independent Codex review gate and do not change the v0.1.0 release.

**Phase 10 refinement:** The required Frama-C/WP target is production `witness_header_status`, not the incomplete exploratory whole-wrapper translation unit. The helper must remain called by the actual `tb_witness_delete` implementation. All WP nonzero goals and native SHA failure-injection tests must pass. Do **not** describe the entire public wrapper, the OpenSSL provider or failure immutability under arbitrary hash behavior as formally proven; the exploratory 35/64 full-wrapper run is documented as incomplete.

## Phase 11 proof discipline

`formal/framac/witness_wrapper_v11.c` is an overlay of **real production C99**; it may assume the explicitly documented external SHA-256 contract, but all internal `fingerprints`, `witness_stage` and wrapper proof goals must be discharged separately with `-wp-rte`. Require the existing Phase 9 and 10 workflow checks, all nonzero goals proved and reviewer approval for the **exact head**. A helper proof does not establish full-wrapper correctness. Unproved goals and solver timeouts block merge; do not weaken contracts or disable runtime safety to make CI green. Preserve v0.1.0.

**Phase 11 executed result:** GitHub Actions run `41314458282` discharged 18/18 `fingerprints`, 23/23 `witness_stage` and 47/47 `tb_witness_delete` WP goals against the exact source blob pinned in `machine/formal/phase11-wp-evidence-v1.json`. Review the **current exact PR head**, not the historical proof-run head, and verify the blob identities remain the same; never mistake this conditional source-level proof for a proof of SHA-256/OpenSSL or a compiled executable.

## Assumption-closure programme (Phase 12 onward)

Maintain [docs/ASSUMPTION_LEDGER.md](docs/ASSUMPTION_LEDGER.md) as the authoritative evidence-vs-assumption map. Phase 12's `tests/formal/test_provider_faults.c` links the actual `src/crypto/fingerprint.c` with real libcrypto and uses GNU `--wrap` **only in test builds** to inject external failures. Its executed GCC/Clang outcomes are *not* a proof of OpenSSL SHA-256 implementation correctness, allocator safety, or all C99 executions. Never upgrade a claim from **observed in tests** to **proved for all inputs** without separately executed formal obligations; preserve source blob identities, negative evidence and immutable `v0.1.0`.

## Phase 13 optional verified-primitive candidate

HACL* SHA2-256 C is vendored under `vendor/hacl-star/` at the exact SHA
`f557259007db9933442dde10aa995c1b00bd3446` (MIT). Run
`python3 tools/check_hacl_source.py` before `make SHA256_BACKEND=hacl test`
and `TOMBSTONE_SHA256_BACKEND=hacl cargo test --workspace --offline --locked`.
Never modify a vendored file without re-pinning every upstream blob and
reviewing the provenance. Keep OpenSSL the default. The adapter,
`src/crypto/fingerprint_hacl.c`, is not automatically covered by upstream
F* verification. Require HACL allocator/error injection, CI parity on actual
x86-64/ARM64 with GCC/Clang, sanitizers, documented upstream F* origin,
explicit C/FFI/ABI refinement obligations, and exact-head independent review.
Do not merge or describe the result as an end-to-end formal SHA proof on
upstream proof reputation or green unit tests alone.
