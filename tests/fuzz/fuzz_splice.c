/* SPDX-License-Identifier: Apache-2.0 */
/* LLVM libFuzzer: manufacture valid splices then perturb the output. */
#include "tombstone/deletion.h"
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define REQUIRE(x) do { if (!(x)) abort(); } while (0)
#define FUZZ_MAX 4096u
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t len)
{
    unsigned char after[FUZZ_MAX], altered[FUZZ_MAX];
    const uint8_t *before;
    size_t n, offset, removed, remaining;
    tb_evidence_v1 ev;
    if (len < 3u || len > FUZZ_MAX) return 0;
    before = data + 2u;
    n = len - 2u;
    offset = (size_t)data[0] % (n + 1u);
    if (offset == n) offset = n - 1u;
    removed = 1u + (size_t)data[1] % (n - offset);
    remaining = n - removed;
    if (offset != 0u) memcpy(after, before, offset);
    if (n - offset - removed != 0u)
        memcpy(after + offset, before + offset + removed, n - offset - removed);
    REQUIRE(tb_witness_delete(before, n, before + offset, removed, offset,
                              after, remaining, &ev) == TB_OK);
    REQUIRE(ev.kind == TB_EVIDENCE_EXPLICIT_DELETE);
    REQUIRE(ev.deleted_offset == offset && ev.deleted_size == removed);
    REQUIRE(tb_observe_transition(before, n, after, remaining, &ev) == TB_OK);
    REQUIRE(ev.kind == TB_EVIDENCE_OBSERVED_TRANSITION);
    REQUIRE(ev.deleted_size == 0u);
    if (remaining != 0u) {
        memcpy(altered, after, remaining);
        altered[remaining / 2u] ^= 0x80u;
        REQUIRE(tb_witness_delete(before, n, before + offset, removed, offset,
                                  altered, remaining, &ev) == TB_ERR_MISMATCH);
    }
    REQUIRE(tb_witness_delete(before, n, before + offset, 0u, offset,
                              after, remaining, &ev) == TB_ERR_ARGUMENT);
    REQUIRE(tb_witness_delete(before, n, before + offset, removed, SIZE_MAX,
                              after, remaining, &ev) == TB_ERR_LENGTH);
    return 0;
}
