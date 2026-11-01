# TOMBSTONE roadmap

**Phases 0–5 have merged. Phase 6 GTK4 desktop is implemented in this PR and awaits review and CI. Phase 7 is planned.**

| Phase | Deliverable | Acceptance gate | Status |
| --- | --- | --- | --- |
| **0 — Foundation** | Human/machine docs, receipt fixtures, project layout | Documentation checks | Merged |
| **1 — C99 SHA-256** | OpenSSL EVP, byte-safe C ABI | Vectors, sanitizers, reproducibility | Merged |
| **2 — C99 deletion witness** | Exact splice checking, observed transitions | Invalid-byte/offset tests | Merged |
| **3 — Receipts/chains** | Restricted RFC 8785 JSON and linked hashes | Golden hashes, malformed/chain tests | Merged |
| **4 — Rust FFI/CLI** | Safe C99 adapter and deterministic headless commands | CLI parity, safe errors | Merged |
| **5 — Rust TUI** | ncurses-guided workflows, inspected receipts, create-new save | PTY and C99 parity | Merged |
| **6 — GTK4 desktop** | Separate native GTK4 frontend using existing C99 evidence workflows | Isolated native build, Xvfb smoke, parity/no-overwrite tests, headless unaffected | In PR; review pending |
| **7 — Hardening/release** | Fuzzing, portability, independent anchoring options | Independent exact-head review and immutable tag | Planned |

## Phase 6 scope

- `apps/gtk` is a **separate Cargo workspace** and remains excluded from the root. `libgtk-4-dev` is required only when building the GUI.
- Six native GTK4 tabs: fingerprint, observe, verify supplied deletion, inspect receipt, verify ordered chain and explicitly save canonical JSON without overwrite.
- The GUI calls the Phase 5 Rust workflow library and established FFI, which exclusively call C99 for evidence and cryptography. No duplicated hash/receipt code, Node.js or third-party Rust crates.
- C99 golden-vector parity, anchored chain tests, input privacy and GTK startup tested under Xvfb. The original headless CLI/TUI/C99 jobs remain intact.
- No automatic deletion, file replacement, remote services, signatures, credentials, history-author authentication or secure erasure claims.

**Next Phase 7:** fuzz input parsers and FFI, independently validate cross-platform replay, review anchoring/privacy tradeoffs and only then consider an immutable release.

See [GTK guide](docs/GTK.md), [invariants](INVARIANTS.md) and [security](SECURITY.md).
