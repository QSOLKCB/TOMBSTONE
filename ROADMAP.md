# TOMBSTONE roadmap

**Phases 0–4 are merged. Phase 5 TUI is implemented in this PR and awaits independent exact-head review.** Phases 6–7 remain planned.

| Phase | Deliverable | Acceptance gate | Status |
| --- | --- | --- | --- |
| **0 — Foundation** | Human/machine documents, receipt schema and fixtures | Documentation tests | Merged |
| **1 — C99 SHA-256** | EVP SHA-256 with versioned byte-safe C ABI | Vectors, sanitizers and reproducibility | Merged |
| **2 — C99 splice evidence** | Exact deletion-splice validation and observed transitions | Negative/overflow/binary tests | Merged |
| **3 — Canonical receipts** | Restricted RFC 8785 JSON and linked hash verification | Golden vectors, chain/parse adversarial tests | Merged |
| **4 — Rust FFI and CLI** | Safe adapter and noninteractive deterministic JSON CLI | C99 parity, I/O privacy and argument regression tests | Merged |
| **5 — Rust ncurses TUI** | Guided evidence creation, receipt inspection, full-chain checks, explicit saving | Independent Rust workflow tests, terminal check, C99 parity | In PR; pending review |
| **6 — Optional GTK4** | Thin desktop UI, same C99 logic | Headless build unaffected, cross-interface parity | Planned |
| **7 — Hardening / release** | Fuzzing, independent anchoring options, portability | Evidence-based review, immutable version tag | Planned |

## Phase 5 specifics

- `apps/tui` contains Rust workflows and a separate terminal executable linked to **system ncursesw** (no third-party Rust crates).
- **All** hashing, splice validation, receipt generation/parsing and chain checking still run in C99 through the existing Rust FFI.
- Interactive selection, scrolling, read-only receipt inspection, optional predecessor commitment, ordered chain validation and optional externally trusted head.
- Explicit `s` export of **only** canonical JSON; create-new (no overwrite), Unix mode 0600. No automatic writes, filesystem deletion, recovery or secure erasure.
- Standalone headless CLI and native C99 remain usable without ncurses; the TUI requires an interactive terminal and TERM configuration.
- C99 and Rust regressions remain mandatory. Phase 6 will add a GTK desktop UI only after Phase 5 is reviewed.

See [TUI guide](docs/TUI.md), [INVARIANTS.md](INVARIANTS.md) and [SECURITY.md](SECURITY.md). A verified splice is not proof of a real-world deletion and an unanchored chain is not authenticated history.
