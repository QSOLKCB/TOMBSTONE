# C99 Phase 2 — explicit deletion witnessing

**Implemented in the Phase 2 PR (subject to review).** The core accepts caller-owned byte buffers and returns an in-memory evidence struct containing SHA-256 fingerprints, lengths and (only for explicit deletion) the supplied verified offset. It does **not** edit files or create serialized receipts.

## Public C99 API

\`include/tombstone/deletion.h\` declares:

- \`tb_evidence_abi_version()\` returning \`TB_EVIDENCE_ABI_VERSION\` (1).
- \`tb_observe_transition(before, before_size, after, after_size, &out)\`.
- \`tb_witness_delete(before, before_size, removed, removed_size, offset, after, after_size, &out)\`.
- \`tb_evidence_v1\` with \`kind\`, raw SHA-256 digests, lengths, deletion size and offset. This is **not** persistent JSON or a machine wire format.

The existing \`tb_status\` enum gains \`TB_ERR_MISMATCH = 6\`. Existing status values and fingerprint ABI version remain unchanged.

## Classification and boundary

| Method | Validated inputs | Evidence kind |
| --- | --- | --- |
| \`tb_observe_transition\` | All before/after bytes directly compared, plus SHA-256 | \`TB_EVIDENCE_UNCHANGED\` or \`TB_EVIDENCE_OBSERVED_TRANSITION\`; deletion fields zero |
| \`tb_witness_delete\` | Before/after, a **nonempty** removed span and its claimed byte offset; exact splice identity | \`TB_EVIDENCE_EXPLICIT_DELETE\`, with removed digest, length and offset |

A witnessed deletion verifies all of:

\`\`\`text
0 < removed_size <= before_size
offset <= before_size - removed_size
after_size == before_size - removed_size
memcmp(before[offset:offset+removed_size], removed) == 0
memcmp(before[0:offset], after[0:offset]) == 0
memcmp(before[offset+removed_size:], after[offset:]) == 0
\`\`\`

The verifier **does not infer deleted bytes or an offset from the two snapshots**, even where a plausible diff exists. In \`aaaa\` -> \`aaa\`, multiple offsets satisfy the splice identity. An externally supplied offset is checked, but **not historically authenticated**.

No-op input to \`tb_observe_transition\` yields \`UNCHANGED\`; an empty \`removed\` span cannot be reported as an explicit deletion. Complete removal of a nonempty buffer **can** produce an explicit deletion with \`after == NULL, after_size == 0\`.

## Minimal C99 example

\`\`\`c
#include "tombstone/deletion.h"
#include <stdio.h>

int main(void) {
    static const unsigned char before[] = {'1',' ','2',' ','3',' ','4',' ','5'};
    static const unsigned char gone[] = {'3',' ','4',' '};
    static const unsigned char after[] = {'1',' ','2',' ','5'};
    tb_evidence_v1 ev;
    char hash[TB_SHA256_HEX_SIZE];
    if (tb_witness_delete(before, sizeof before, gone, sizeof gone, 4,
                          after, sizeof after, &ev) != TB_OK ||
        tb_sha256_hex(ev.deleted_sha256, hash) != TB_OK)
        return 1;
    printf("removed span SHA-256: %s\n", hash);
    return 0;
}
\`\`\`

Compile after \`make\`:

\`\`\`sh
cc -std=c99 -Iinclude example.c build/libtombstone.a $(pkg-config --libs openssl) -o example
\`\`\`

## Error and privacy contract

- \`TB_ERR_ARGUMENT\`: null output pointer; nonzero-size null input; null/zero-length removed span.
- \`TB_ERR_LENGTH\`: out-of-bounds offset, removed span larger than before, or an input length/offset above the proposed receipt schema's integer-safe limit (\`2^53-1\`). No buffer is dereferenced before the range checks.
- \`TB_ERR_MISMATCH\`: requested splice cannot produce the supplied after buffer, including a wrong byte or wrong expected after length.
- \`TB_ERR_MEMORY\` / \`TB_ERR_CRYPTO\`: underlying SHA-256 failure.
- On **any failure**, the output evidence struct is untouched; all inputs are read-only, borrowed, and never persisted by the library. Output and input memory must be disjoint; the caller guarantees valid pointer extents.
- \`deleted_size\`, \`deleted_offset\`, and \`deleted_sha256\` are zero for observed/no-op evidence and must be treated as **absent** except when \`kind == TB_EVIDENCE_EXPLICIT_DELETE\`.
- The returned struct is in-memory ABI data, not a canonical serialized receipt. Phase 3 implements the proposed JSON receipts/linked chain.

Neither the hashing nor witnessing APIs erase data or prove an editor operation took place. They cannot certify author identity, time, secure erasure, confidentiality or independent chain anchoring. See [security](../SECURITY.md) and [threat model](THREAT_MODEL.md).
