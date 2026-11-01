/* SPDX-License-Identifier: Apache-2.0 */
/* Deliberate provider-failure injection against actual production C99 body.
 * The stub is NEVER linked into the release engine.
 */
#include "tombstone/deletion.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { \
  fprintf(stderr,"FAIL: %s at %d\n",#x,__LINE__); exit(1); \
} } while (0)
static unsigned calls, fail_call;
static tb_status fail_status;
tb_status tb_sha256_bytes(const void *data, size_t length,
                          unsigned char out[TB_SHA256_DIGEST_SIZE])
{
    (void)data;
    (void)length;
    ++calls;
    if (calls == fail_call) return fail_status;
    memset(out, (int)(0x10u + calls), TB_SHA256_DIGEST_SIZE);
    return TB_OK;
}
#include "../../src/core/deletion.c"

int main(void)
{
    static const char before[] = "1 2 3 4 5";
    static const char removed[] = "3 4 ";
    static const char after[] = "1 2 5";
    static const char altered[] = "1 2 6";
    tb_evidence_v1 out, pristine;
    unsigned fail;
    tb_status st;
    memset(&pristine, 0xa5, sizeof(pristine));
    for (fail = 1u; fail <= 3u; ++fail) {
        out = pristine; calls = 0u; fail_call = fail;
        fail_status = fail == 2u ? TB_ERR_MEMORY : TB_ERR_CRYPTO;
        st = tb_witness_delete(before, 9u, removed, 4u, 4u, after, 5u, &out);
        CHECK(st == fail_status);
        CHECK(calls == fail);
        CHECK(memcmp(&out, &pristine, sizeof(out)) == 0);
    }
    out = pristine; calls = 0u; fail_call = 0u;
    CHECK(tb_witness_delete(before, 9u, removed, 4u, 4u, after, 5u, &out) == TB_OK);
    CHECK(calls == 3u);
    CHECK(out.kind == TB_EVIDENCE_EXPLICIT_DELETE);
    CHECK(out.before_size == 9u && out.after_size == 5u);
    CHECK(out.deleted_size == 4u && out.deleted_offset == 4u);
    CHECK(out.before_sha256[0] == 0x11u);
    CHECK(out.after_sha256[0] == 0x12u);
    CHECK(out.deleted_sha256[0] == 0x13u);
    out = pristine; calls = 0u;
    CHECK(tb_witness_delete(before, 9u, removed, 4u, 99u, after, 5u, &out) == TB_ERR_LENGTH);
    CHECK(calls == 0u && memcmp(&out, &pristine, sizeof(out)) == 0);
    CHECK(tb_witness_delete(before, 9u, removed, 4u, 4u, after, 4u, &out) == TB_ERR_MISMATCH);
    CHECK(calls == 0u && memcmp(&out, &pristine, sizeof(out)) == 0);
    CHECK(tb_witness_delete(before, 9u, removed, 4u, 4u, altered, 5u, &out) == TB_ERR_MISMATCH);
    CHECK(calls == 0u && memcmp(&out, &pristine, sizeof(out)) == 0);
    CHECK(tb_witness_delete(before, 9u, removed, 0u, 4u, after, 5u, &out) == TB_ERR_ARGUMENT);
    CHECK(calls == 0u && memcmp(&out, &pristine, sizeof(out)) == 0);
    CHECK(tb_witness_delete(before, 9u, NULL, 4u, 4u, after, 5u, &out) == TB_ERR_ARGUMENT);
    CHECK(calls == 0u && memcmp(&out, &pristine, sizeof(out)) == 0);
    puts("PASS: actual wrapper's hash failures 1/2/3 leave output unchanged");
    puts("PASS: error precedence and success metadata under synthetic provider");
    return 0;
}
