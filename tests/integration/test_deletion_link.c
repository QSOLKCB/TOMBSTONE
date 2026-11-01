/* SPDX-License-Identifier: Apache-2.0 */
/* A standalone consumer of the Phase 2 public C header and static archive. */
#include "tombstone/deletion.h"
#include <stdio.h>
#include <string.h>

int main(void)
{
    static const unsigned char before[] = {0, 1, 2, 3, 255};
    static const unsigned char removed[] = {1, 2, 3};
    static const unsigned char after[] = {0, 255};
    tb_evidence_v1 ev;
    char hex[TB_SHA256_HEX_SIZE];

    if (tb_witness_delete(before, sizeof(before), removed, sizeof(removed),
                          1u, after, sizeof(after), &ev) != TB_OK ||
        ev.kind != TB_EVIDENCE_EXPLICIT_DELETE ||
        ev.deleted_size != 3u || ev.deleted_offset != 1u ||
        tb_sha256_hex(ev.deleted_sha256, hex) != TB_OK ||
        strlen(hex) != 64u) {
        fputs("FAIL: external Phase 2 C99 consumer\n", stderr);
        return 1;
    }
    if (tb_observe_transition(before, sizeof(before), after, sizeof(after),
                              &ev) != TB_OK ||
        ev.kind != TB_EVIDENCE_OBSERVED_TRANSITION ||
        ev.deleted_size != 0u) {
        fputs("FAIL: observed transition wrongly inferred deletion\n", stderr);
        return 1;
    }
    puts("PASS: external C99 deletion evidence ABI and provenance boundary");
    return 0;
}
