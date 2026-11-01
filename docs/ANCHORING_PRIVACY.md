# Anchoring and confidentiality — limits of v1

The receipt commitment is `SHA256("TOMBSTONE-RECEIPT-V1\n" ||
canonical_receipt_without_receipt_hash)`, with schema-limited RFC 8785
canonical JSON. Each non-genesis receipt includes its predecessor hash.

| Attack or assumption | What v1 establishes |
| --- | --- |
| Single receipt modified | Self-digest fails |
| Middle receipt reordered | Link or digest verification fails |
| Whole chain regenerated | **Not detectable** from rewritten chain alone |
| Independently trusted head retained | Divergence from that head can be detected |
| Short secret removed | Bare SHA-256 is dictionary-guessable |
| Fabricated caller buffers | A valid splice relationship does not prove the event happened |
| Source bytes in swap/backups/undo | TOMBSTONE does not erase them |

## Optional manual anchoring

After full-chain verification, retain the final **receipt_hash** separately
from the editable chain, e.g. in an independent controlled audit log, signed
message or other externally preserved location. Later pass it with
`--trusted-head`. Keeping the hash beside the editable chain is NOT
independent anchoring.

The receipt's domain-separated `receipt_hash` is NOT the SHA-256 of the JSON
file bytes. The latter varies with whitespace/newlines, while the former
excludes the receipt_hash property and canonicalizes the body.

No signing service, timestamp trust, hardware attestation or remote immutable
store is implemented. Optional keyed commitments could reduce guessing of
short secrets but would need explicit key management and a new protocol.

## Sensitive metadata

Receipts omit deleted plaintext, original file paths and identities, but
digests of low-entropy values may still disclose information by guessing.
Treat such receipts as potentially sensitive metadata.
