# Phase 3 — canonical TOMBSTONE receipts

**Implementation:** C99 \`include/tombstone/receipt.h\` and \`src/encoding/receipt.c\`. No Rust CLI/TUI, GUI, real-file deletion, archive, signing or network protocol is introduced.

## Concrete API

- \`tb_receipt_create(evidence, previous_hash, &receipt)\`: derives the canonical digest from a validated Phase 2 evidence struct; \`previous_hash == NULL\` creates genesis.
- \`tb_receipt_encode(&receipt, output, output_capacity, &written)\`: deterministic compact JSON; no implicit trailing NUL/newline. Returns \`TB_ERR_LENGTH\` if capacity is insufficient without partially writing the buffer.
- \`tb_receipt_parse(bytes, size, &receipt)\`: strictly parses allowed v1 keys, typed values and schema semantics; recomputes and checks the stored digest.
- \`tb_receipt_verify_chain(receipts, count, trusted_head)\`: checks each receipt digest, genesis status and predecessor link; an optional external \`trusted_head\` checks the last receipt.
- \`tb_receipt_abi_version()\` returns 1. Status \`TB_ERR_FORMAT = 7\` is added without changing prior values.

Results use an in-memory \`tb_receipt_v1\` struct containing the Phase 2 \`tb_evidence_v1\`, an optional predecessor digest and the current receipt digest. **Do not persist the struct's memory representation**; use \`tb_receipt_encode\`.

## Version 1 canonical encoding

The receipt shape is fixed by [receipt-v1.schema.json](../machine/schemas/receipt-v1.schema.json). Allowed JSON values are fixed ASCII strings, lowercase 64-character hexadecimal digests, \`null\`, and nonnegative integers no larger than 2^53−1. For this restricted value/key set, lexicographically sorted fixed keys, unescaped ASCII strings and minimal decimal integer tokens yield exactly the RFC 8785 JSON Canonicalization Scheme representation.

**This is a schema-specific RFC 8785 encoder, not an arbitrary JSON or Unicode canonicalizer.** The parser accepts field reordering, JSON whitespace and ASCII JSON \`\\u\` escapes for the permitted literals. It rejects duplicate and unknown keys (including escaped duplicates), unsupported versions, extra fields, non-ASCII strings, surrogates, malformed escapes, decimal fractions, exponent notation, integer overflow, incorrect digest lengths/hex, and content/hash mismatches. Output is always canonical, regardless of input field ordering.

The body hash excludes \`receipt_hash\`:

\`\`\`text
SHA256( ASCII("TOMBSTONE-RECEIPT-V1\n") || RFC8785_JCS(receipt_without_receipt_hash) )
\`\`\`

The parser verifies the body hash but does not by itself verify a chain; use \`tb_receipt_verify_chain\` for that.

## What the chain proves—and what it does not

Each non-genesis receipt includes \`previous_receipt_hash\`, the **32-byte SHA-256 digest** of its direct predecessor, encoded as lowercase hex in JSON. The verifier checks every receipt’s self-hash and all links. It **requires a genesis receipt** at index zero; a truncated suffix alone cannot be treated as a complete chain.

**Local-only verification cannot detect rewriting the entire chain.** Supply a trusted final hash from an independent channel to detect divergence relative to that head. Even with anchoring, signatures/authorship, actual file erasure, timestamps, real-world editor activity and deleted-text confidentiality are not proven. The previous phase’s \`explicit-delete\` means a verified **caller-provided splice identity**, not an authenticated deletion event.

## Test evidence

\`make test\` exercises all three preexisting [machine examples](../machine/examples/), hashes cross-checked against independent Python-generated vectors, round-trip parse/encode, broken predecessor links, invalid anchors, modified body digests, truncated JSON, invalid versions, bad sizes, buffer-length rejection, forged Phase 2 evidence and regression tests. The GitHub workflow runs GCC/Clang, ASan+UBSan and deterministic archive builds.

No file I/O exists in the C99 engine; the test harness only opens **public synthetic fixture files** from the repository.
