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

## Immediate development commands

\`\`\`sh
make docs-check
\`\`\`

This validates **documentation fixtures only**. There is no buildable C or Rust product yet. The first implementation PR should add C99 SHA-256 vectors and deterministic receipt encoding/verification tests, then update this file with real build commands.
