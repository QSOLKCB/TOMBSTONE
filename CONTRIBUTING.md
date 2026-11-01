# Contributing

TOMBSTONE is currently a documentation-first foundation. Read [AGENTS.md](AGENTS.md), [ARCHITECTURE.md](ARCHITECTURE.md), [INVARIANTS.md](INVARIANTS.md) and [SECURITY.md](SECURITY.md) before proposing functionality.

Keep PRs narrow, attach exact reproduction steps, distinguish executed tests from planned ones, preserve provenance, and document wire-contract changes with a decision record under \`docs/decisions/\`. For documentation changes, run \`make docs-check\`. Never submit real deleted secrets as fixtures. Keep generated receipts machine-only under \`machine/\`, prose under \`docs/\`, and all evidence-relevant computation in future C99 core code.

Apache-2.0 is the current repository license.
