# Contributing

TOMBSTONE's C99 Phases 1–3 are merged. Phase 4 adds a safe Rust FFI layer and noninteractive CLI (review pending). Rust TUI/optional GTK remain planned. Read [AGENTS.md](AGENTS.md), [ARCHITECTURE.md](ARCHITECTURE.md), [INVARIANTS.md](INVARIANTS.md) and [SECURITY.md](SECURITY.md) before proposing functionality.

Keep PRs narrow, attach exact reproduction steps, distinguish executed tests from planned ones, preserve provenance, and document wire-contract changes with a decision record under \`docs/decisions/\`. Run \`make docs-check\` for documentation, and run \`make test\`, \`make sanitizer-test\` and \`make reproducibility\` for changes affecting C99 code. For Rust/CLI changes also run `cargo test --workspace --locked --offline`. Never submit real deleted secrets as fixtures. Keep generated receipts machine-only under \`machine/\`, prose under \`docs/\`, and all evidence-relevant computation in future C99 core code.

Apache-2.0 is the current repository license.
