/* SPDX-License-Identifier: Apache-2.0 */
/* Phase 8: bounded symbolic checking of UNMODIFIED src/core/deletion.c.
 * Dependency model: SHA-256 succeeds and writes a fixed 32-byte digest.
 * This is NOT a proof of SHA-256, OpenSSL or unbounded C99 correctness.
 */
#include "tombstone/deletion.h"
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#define FORMAL_CAP 4u
extern unsigned int nondet_uint(void);
extern unsigned char nondet_uchar(void);
void __CPROVER_assume(int);
void __CPROVER_assert(int, const char *);

tb_status tb_sha256_bytes(const void *buffer, size_t size,
                          unsigned char digest[TB_SHA256_DIGEST_SIZE])
{
    (void)buffer;
    (void)size;
    memset(digest, 0x5a, TB_SHA256_DIGEST_SIZE);
    return TB_OK;
}
/* Include actual C99 bodies rather than a manually translated substitute. */
#include "../../src/core/deletion.c"

/* Independent index-based byte oracle. */
static int oracle(const unsigned char b[FORMAL_CAP], unsigned bn,
                  const unsigned char r[FORMAL_CAP], unsigned rn,
                  unsigned offset, const unsigned char a[FORMAL_CAP],
                  unsigned an)
{
    unsigned i;
    if (rn == 0u || rn > bn || offset > bn - rn || an != bn - rn) return 0;
    for (i = 0u; i < rn; ++i)
        if (b[offset + i] != r[i]) return 0;
    for (i = 0u; i < an; ++i)
        if (a[i] != b[i < offset ? i : i + rn]) return 0;
    return 1;
}

void check_witness(void)
{
    unsigned char b[FORMAL_CAP], r[FORMAL_CAP], a[FORMAL_CAP];
    unsigned bn = nondet_uint(), rn = nondet_uint();
    unsigned an = nondet_uint(), offset = nondet_uint();
    tb_evidence_v1 output, original;
    tb_status status, expected;
    unsigned i;
    __CPROVER_assume(bn <= FORMAL_CAP && rn <= FORMAL_CAP &&
                     an <= FORMAL_CAP && offset <= FORMAL_CAP + 1u);
    for (i = 0u; i < FORMAL_CAP; ++i) {
        b[i] = nondet_uchar();
        r[i] = nondet_uchar();
        a[i] = nondet_uchar();
    }
    memset(&output, 0xa5, sizeof(output));
    memset(&original, 0xa5, sizeof(original));
    status = tb_witness_delete(b, bn, r, rn, offset, a, an, &output);
    if (rn == 0u) expected = TB_ERR_ARGUMENT;
    else if (rn > bn || offset > bn - rn) expected = TB_ERR_LENGTH;
    else if (oracle(b, bn, r, rn, offset, a, an)) expected = TB_OK;
    else expected = TB_ERR_MISMATCH;
    __CPROVER_assert(status == expected,
                     "witness status agrees with independent splice relation");
    if (status == TB_OK) {
        __CPROVER_assert(output.kind == TB_EVIDENCE_EXPLICIT_DELETE,
                         "verified witness is explicit-delete");
        __CPROVER_assert(output.before_size == bn && output.after_size == an &&
                         output.deleted_size == rn && output.deleted_offset == offset,
                         "successful witness reports exact lengths and offset");
    } else {
        __CPROVER_assert(memcmp(&output, &original, sizeof(output)) == 0,
                         "error does not modify any output byte");
    }
}

void check_observe(void)
{
    unsigned char b[FORMAL_CAP], a[FORMAL_CAP];
    unsigned bn = nondet_uint(), an = nondet_uint();
    tb_evidence_v1 output;
    tb_status status;
    unsigned i;
    int equal;
    __CPROVER_assume(bn <= FORMAL_CAP && an <= FORMAL_CAP);
    for (i = 0u; i < FORMAL_CAP; ++i) {
        b[i] = nondet_uchar();
        a[i] = nondet_uchar();
    }
    equal = bn == an;
    for (i = 0u; i < bn && equal; ++i)
        if (b[i] != a[i]) equal = 0;
    status = tb_observe_transition(b, bn, a, an, &output);
    __CPROVER_assert(status == TB_OK,
                     "observe succeeds when hash dependency succeeds");
    __CPROVER_assert(output.kind == (equal ? TB_EVIDENCE_UNCHANGED :
                                   TB_EVIDENCE_OBSERVED_TRANSITION),
                     "observed classification reflects exact byte equality");
    __CPROVER_assert(output.deleted_size == 0u && output.deleted_offset == 0u,
                     "observation never fabricates a deleted span");
}
