/* SPDX-License-Identifier: Apache-2.0 */
#include "tombstone/deletion.h"

#include <stdint.h>
#include <string.h>

unsigned int tb_evidence_abi_version(void)
{
    return TB_EVIDENCE_ABI_VERSION;
}

static int valid_buffer(const void *p, size_t n)
{
    return p != NULL || n == 0u;
}

static int valid_size(size_t n)
{
    /* Check before casting: works on both 32- and 64-bit size_t. */
    return n <= TB_EVIDENCE_MAX_BYTES;
}

static tb_status fingerprints(const void *before, size_t before_size,
                              const void *after, size_t after_size,
                              tb_evidence_v1 *temp)
{
    tb_status st = tb_sha256_bytes(before, before_size, temp->before_sha256);
    if (st != TB_OK) {
        return st;
    }
    return tb_sha256_bytes(after, after_size, temp->after_sha256);
}

tb_status tb_observe_transition(const void *before, size_t before_size,
                                const void *after, size_t after_size,
                                tb_evidence_v1 *out)
{
    tb_evidence_v1 tmp;
    tb_status st;
    if (out == NULL || !valid_buffer(before, before_size) ||
        !valid_buffer(after, after_size)) {
        return TB_ERR_ARGUMENT;
    }
    if (!valid_size(before_size) || !valid_size(after_size)) {
        return TB_ERR_LENGTH;
    }

    /* Observe actual bytes, not only hashes: a hash cannot prove equality. */
    memset(&tmp, 0, sizeof(tmp));
    tmp.kind = before_size == after_size &&
               (before_size == 0u || memcmp(before, after, before_size) == 0)
                   ? TB_EVIDENCE_UNCHANGED : TB_EVIDENCE_OBSERVED_TRANSITION;
    tmp.before_size = before_size;
    tmp.after_size = after_size;
    st = fingerprints(before, before_size, after, after_size, &tmp);
    if (st != TB_OK) {
        return st;
    }
    *out = tmp;
    return TB_OK;
}

tb_status tb_witness_delete(const void *before, size_t before_size,
                            const void *removed, size_t removed_size,
                            size_t offset,
                            const void *after, size_t after_size,
                            tb_evidence_v1 *out)
{
    const unsigned char *b;
    const unsigned char *a;
    size_t suffix_size;
    tb_evidence_v1 tmp;
    tb_status st;

    if (out == NULL || !valid_buffer(before, before_size) ||
        removed == NULL || removed_size == 0u ||
        !valid_buffer(after, after_size)) {
        return TB_ERR_ARGUMENT;
    }
    if (!valid_size(before_size) || !valid_size(after_size) ||
        !valid_size(removed_size) || !valid_size(offset) ||
        removed_size > before_size || offset > before_size - removed_size) {
        return TB_ERR_LENGTH;
    }
    if (after_size != before_size - removed_size) {
        return TB_ERR_MISMATCH;
    }

    b = (const unsigned char *)before;
    a = (const unsigned char *)after;
    suffix_size = before_size - offset - removed_size;
    if (memcmp(b + offset, removed, removed_size) != 0 ||
        (offset != 0u && memcmp(b, a, offset) != 0) ||
        (suffix_size != 0u &&
         memcmp(b + offset + removed_size, a + offset, suffix_size) != 0)) {
        return TB_ERR_MISMATCH;
    }

    memset(&tmp, 0, sizeof(tmp));
    tmp.kind = TB_EVIDENCE_EXPLICIT_DELETE;
    tmp.before_size = before_size;
    tmp.after_size = after_size;
    tmp.deleted_size = removed_size;
    tmp.deleted_offset = offset;

    st = fingerprints(before, before_size, after, after_size, &tmp);
    if (st != TB_OK) {
        return st;
    }
    st = tb_sha256_bytes(removed, removed_size, tmp.deleted_sha256);
    if (st != TB_OK) {
        return st;
    }
    *out = tmp;
    return TB_OK;
}
