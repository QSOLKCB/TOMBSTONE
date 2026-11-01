# TOMBSTONE roadmap

**Phases 0–3 are merged. Phase 4 is implemented in this PR and awaits independent review and CI.** Phases 5–7 remain planned.

| Phase | Deliverable | Acceptance gate | Status |
| --- | --- | --- | --- |
| **0 — Foundation** | Human docs, machine contract, fixture vectors, repository structure and art | Documentation checks | Merged |
| **1 — C99 fingerprinting** | SHA-256 EVP, binary-safe public C ABI | NIST vectors, sanitizers, reproducible builds | Merged |
| **2 — C99 witnessed deletion** | Exact splice and observed-transition classification | Null, empty, repeated bytes, offset, overflow and binary tests | Merged |
| **3 — Canonical receipts** | Restricted RFC 8785 JSON, strict parse and linked verification | Golden fixtures, malformed input, anchored chains | Merged |
| **4 — Rust FFI / noninteractive CLI** | Safe adapter and deterministic CLI for agents and humans | C99 parity, pipe-safe stdout/stderr, stable exit codes, adversarial CLI tests | Implemented in PR; review/CI gate |
| **5 — Rust TUI** | Human-oriented guided workflow and receipt inspection | Accessibility and C99 parity | Planned |
| **6 — Optional GTK4** | Thin desktop interface using same FFI | No duplicated logic; headless operation preserved | Planned |
| **7 — Hardening / release** | Fuzzing, cross-platform reproducibility, anchoring and packaging | Independent review and immutable tag | Planned |

## Phase 4 scope

- Cargo workspace with \`bindings/rust\` (safe Rust FFI) and \`apps/cli\` (noninteractive binary) and **no external Rust crates**. Build script compiles unchanged C99 sources and links system OpenSSL.
- Safe wrapper exposes hash, observe, witness deletion, canonical receipt creation/parsing, and full ordered-chain verification. It returns native C99 errors without making independent cryptographic decisions.
- CLI accepts file or stdin input; \`hash\`, \`observe\`, \`delete\`, \`verify\`, \`verify-chain\`. For evidence-producing operations stdout is precisely one deterministic JSON object and newline; failures exit nonzero and emit no success JSON.
- Rust unit tests and black-box CLI integration tests cover original Phase 3 receipt hashes, binary stdin, explicit deletion, observed-only classification, invalid offsets, duplicate-field records, reordered chains and mismatched trusted heads.
- TUI/GTK, agent network automation, timestamps, signatures, automatic data deletion and remote anchoring are explicitly out of scope.

## Next steps

Phase 5 adds a Rust TUI over the same FFI; Phase 6 adds optional GTK. Phase 7 performs further adversarial and portability hardening before any immutable release. Keep evidence receipts separate from human narrative and preserve the C99 source-of-truth rule.

See [docs/CLI.md](docs/CLI.md), [AGENTS.md](AGENTS.md) and [INVARIANTS.md](INVARIANTS.md).
