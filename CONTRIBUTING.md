# Contributing

TOMBSTONE has a documentation foundation and a Phase 1 C99 SHA-256 and Phase 2 deletion-splice verification are merged. Phase 3 introduces JSON receipt/chain validation (review pending); Rust interfaces remain planned. Read [AGENTS.md](AGENTS.md), [ARCHITECTURE.md](ARCHITECTURE.md), [INVARIANTS.md](INVARIANTS.md) and [SECURITY.md](SECURITY.md) before proposing functionality.

Keep PRs narrow, attach exact reproduction steps, distinguish executed tests from planned ones, preserve provenance, and document wire-contract changes with a decision record under \`docs/decisions/\`. Run \`make docs-check\` for documentation, and run \`make test\`, \`make sanitizer-test\` and \`make reproducibility\` for changes affecting the Phase 1 C99 fingerprint library. Never submit real deleted secrets as fixtures. Keep generated receipts machine-only under \`machine/\`, prose under \`docs/\`, and all evidence-relevant computation in future C99 core code.

Apache-2.0 is the current repository license.
