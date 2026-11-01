# Receipt format v1 — candidate design, not released

Phase 2 returns `tb_evidence_v1` (in-memory C99) with before/after hashes and optional verified removed-span hash and offset. It does **not** create JSON receipts; the following Phase 3 contract is still a proposal.

The machine source of truth is [the JSON Schema](../machine/schemas/receipt-v1.schema.json), and the separately stored [JSON examples](../machine/examples/) are illustrative test vectors. This page is human prose, **not a second machine contract**.

## Record fields

- \`format\`: exactly \`tombstone.receipt\`.
- \`version\`: integer \`1\`.
- \`kind\`: \`explicit-delete\`, \`observed-transition\`, or \`unchanged\`.
- \`before\` / \`after\`: raw-byte SHA-256 lowercase hex and number of bytes.
- \`deleted\`: null except for an explicitly witnessed deletion; then SHA-256, byte length (positive), and byte offset in the before stream.
- \`previous_receipt_hash\`: SHA-256 hex of preceding receipt or null for genesis.
- \`receipt_hash\`: hash of canonical receipt body without this field.

The proposed receipt digest is

\`\`\`text
SHA256( ASCII("TOMBSTONE-RECEIPT-V1\n") || RFC8785_JCS(body_without_receipt_hash) )
\`\`\`

where \`||\` is byte concatenation, and RFC 8785 defines canonical JSON UTF-8 serialization. All candidate v1 fields use fixed ASCII strings, lowercase hex, null and bounded nonnegative integers, simplifying cross-runtime fixture checks. A parser for the eventual product must reject duplicate fields and unknown versions. It must not accept altered canonicalization or different integer interpretations.

The illustrative chain is deliberately ordered: \`explicit-delete-v1.json\` (genesis), \`observed-transition-v1.json\`, \`unchanged-v1.json\`. The latter two link to the prior receipt's exact hash. These are *examples*, not records of live filesystem events. **Some examples share before/after bytes to illustrate differences in knowledge, not a literal editing history across the examples.**

## Validation layers

JSON Schema checks shape; cryptographic logic checks raw digests; splice verification checks that \`before == prefix || deleted || suffix\` and \`after == prefix || suffix\`; chain verification checks previous hashes. The docs fixture script checks only known illustrative data and constrained canonical hash calculations; it does not implement full RFC 8785 or general JSON Schema processing and **must not be shipped as a verifier**.

A receipt is evidence of an assertion under the witnessing system. Without trusted observation or a separately anchored chain it is not standalone proof of the claimed real-world action.
