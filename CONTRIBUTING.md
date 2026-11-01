# Contributing

TOMBSTONE's C99 Phases 1–3 are merged. Phase 4 Rust FFI and CLI are merged. Phase 5 adds an interactive Rust ncurses TUI (review pending); optional GTK remains planned. Read [AGENTS.md](AGENTS.md), [ARCHITECTURE.md](ARCHITECTURE.md), [INVARIANTS.md](INVARIANTS.md) and [SECURITY.md](SECURITY.md) before proposing functionality.

Keep PRs narrow, attach exact reproduction steps, distinguish executed tests from planned ones, preserve provenance, and document wire-contract changes with a decision record under \`docs/decisions/\`. Run \`make docs-check\` for documentation, and run \`make test\`, \`make sanitizer-test\` and \`make reproducibility\` for changes affecting C99 code. For Rust changes run `cargo test --workspace --locked --offline` with libncurses-dev installed. CLI-only checks can use `cargo test -p tombstone-ffi -p tombstone-cli --offline --locked` without ncurses. Never submit real deleted secrets as fixtures. Keep generated receipts machine-only under \`machine/\`, prose under \`docs/\`, and all evidence-relevant computation in future C99 core code.

Apache-2.0 is the current repository license.
