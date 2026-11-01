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

## C99 Phases 1–3 engine and test commands

\`make\` builds the native static archive. Requires OpenSSL development headers and pkg-config. C99 SHA-256 resides in `src/crypto/fingerprint.c`; verified splice and classification in `src/core/deletion.c`. Public headers additionally include `include/tombstone/receipt.h`; JSON encoding and parser live in `src/encoding/receipt.c`.

\`\`\`sh
make
make test
make sanitizer-test
make reproducibility
make docs-check
\`\`\`

**Implemented:** C99 one-shot/streamed SHA-256, exact-splice verification with required nonempty removed span and offset, and observed-change/no-op classification without deletion inference. Return only SHA-256, sizes and offset; failure leaves output untouched.

**Not implemented:** historical proof of editing, filesystem deletion, Rust CLI/TUI or GTK. Canonical v1 JSON and hash-link verification are implemented; a trusted head from outside the local chain remains required to detect wholesale rewriting. Never claim that before/after hashes prove removed bytes.

Review the **exact head SHA** and distinguish executed tests from inferred results. Keep each future milestone narrow, evidence-gated and independently reviewable.
