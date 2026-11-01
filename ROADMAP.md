# TOMBSTONE roadmap

Status is tracked per phase. **Phases 0 and 1 are implemented in source; Phase 1 remains subject to PR review/merge and release gates.** All later stages are unimplemented.

| Phase | Target | Acceptance gate | Current status |
| --- | --- | --- | --- |
| **0 — Foundation** | Architecture, invariants, security, machine receipt proposal, prose/docs, banner, directories, fixtures | Documentation fixture validation | Complete (merged foundation) |
| **1 — C99 fingerprinting** | Binary-safe SHA-256 core with vetted backend, public minimal C ABI, input length and errors | C99 known-answer vectors, sanitizer build, reproducible static archive | Implemented in Phase 1 PR; review/CI gate |
| **2 — C99 explicit deletion** | Verified splice operations; distinguish witnessed deletion from observed transitions | Binary, repeated-byte, replacement, null, empty and overflow cases | Planned |
| **3 — Canonical receipts + chains** | Strict versioned RFC 8785 receipt encoding, decoding and verification | Golden vectors, malicious records, chain tampering | Planned |
| **4 — Rust adapter and CLI** | Thin safe FFI, deterministic CLI/JSON for agents and scripts | CLI tests, C99 parity, stderr/stdout separation | Planned |
| **5 — Rust TUI** | Human inspection and guided witnessed-deletion workflows | Same receipts as CLI, terminal fallback | Planned |
| **6 — Optional GTK4** | Thin desktop presentation | No semantic drift or GTK dependency for headless build | Planned |
| **7 — Hardening / v1 release** | Cross-platform replay, fuzzing, anchor/signature options and packaging | Independent review, immutable tag, release proof | Planned |

## Phase 1 delivered scope

- \`include/tombstone/fingerprint.h\`: versioned, explicit-length C99 API.
- \`src/crypto/fingerprint.c\`: OpenSSL EVP SHA-256 one-shot and streaming wrapper.
- Tests for SHA-256 empty input, \`abc\`, FIPS longer input, one million \`a\` bytes, binary data including NUL/high bytes, state/error behaviour, and public static-library linkage.
- Reproducibility check comparing two freshly built deterministic \`.a\` archives.
- GCC/Clang CI jobs and ASan/UBSan job.

This phase computes fingerprints only; **it neither deletes data nor claims knowledge of removed bytes**. Output hashes are based solely on the bytes the caller provides. No receipt serialization is implemented.

## Decisions and explicit exclusions

- Receipts must not include deleted plaintext or identifying paths; public synthetic fixtures are exceptions used for testing.
- Secure erasure, undelete, system-wide editor hooks, remote monitoring, signatures, and authorship/timing proofs are not promised.
- Guessable removed content is susceptible to dictionary attacks when represented by bare SHA-256 hashes.
- Linux-first CI; C99 core avoids Linux-specific API use. OpenSSL is linked as a vetted backend, not vendored or reinvented.
- Smaller PRs are encouraged; each phase requires executed evidence.

## Near-term next PRs

1. Phase 2: C99 verified byte splice and evidence classification, including adversarial tests.
2. Phase 3: strict RFC 8785 receipt creation/parsing/chain verification.
3. Phase 4: Rust safe FFI and noninteractive CLI, followed by TUI.

See [docs/decisions/0001-c99-core-rust-frontends.md](docs/decisions/0001-c99-core-rust-frontends.md).
