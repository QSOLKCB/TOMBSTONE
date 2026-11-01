# Machine-readable material

This directory is **machine-oriented**. It contains a versioned v1 JSON Schema and three synthetic golden receipt examples — no human-facing essay or narrative fields inside protocol records.

- \`schemas/receipt-v1.schema.json\`: version 1 C99 receipt profile (pre-release).
- \`examples/explicit-delete-v1.json\`: publicly constructed witnessed-splice example.
- \`examples/observed-transition-v1.json\`: same byte fingerprints, but no deleted-span claim.
- \`examples/unchanged-v1.json\`: no-op, no deletion claim.
- The three examples form an illustrative hash chain in the listed order.

For human context, see [docs/RECEIPT_FORMAT.md](../docs/RECEIPT_FORMAT.md). JSON Schema is not a verifier for SHA-256 content, actual splice provenance or chain ancestry. Phase 3 C99 now encodes, parses, and verifies the restricted v1 shape. The format remains subject to exact-head review and a deliberate tagged release; do not infer cryptographic authentication of the real-world deletion event.
