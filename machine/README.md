# Machine-readable material

This directory is **machine-oriented**. It contains a proposed JSON Schema and JSON receipt examples — no human-facing essay or narrative fields inside protocol records.

- \`schemas/receipt-v1.schema.json\`: proposed **version 1 candidate**.
- \`examples/explicit-delete-v1.json\`: publicly constructed witnessed-splice example.
- \`examples/observed-transition-v1.json\`: same byte fingerprints, but no deleted-span claim.
- \`examples/unchanged-v1.json\`: no-op, no deletion claim.
- The three examples form an illustrative hash chain in the listed order.

For human context, see [docs/RECEIPT_FORMAT.md](../docs/RECEIPT_FORMAT.md). JSON Schema is not a verifier for SHA-256 content, actual splice provenance or chain ancestry. The format is not stable until an explicit tagged release.
