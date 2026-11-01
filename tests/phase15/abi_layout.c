/* SPDX-License-Identifier: Apache-2.0 */
/* Phase 15: native C99 ABI facts, compiled/executed by the actual target CC.
 * This executable is a TEST ORACLE, not linked into TOMBSTONE production.
 * offsetof(struct { char c; TYPE value; }, value) is C99 alignment.
 */
#include "tombstone/receipt.h"
#include <stddef.h>
#include <stdio.h>

#define ALIGNOF_TYPE(T) offsetof(struct { char c; T value; }, value)
#define METRIC(name, value) do { \
    if (printf("%s=%zu\n", name, (size_t)(value)) < 0) return 1; \
} while (0)
#define FIELD(T, member) METRIC(#T "." #member, offsetof(T, member))
#define SIZE(T) METRIC(#T ".size", sizeof(T))
#define ALIGN(T) METRIC(#T ".align", ALIGNOF_TYPE(T))

int main(void)
{
    SIZE(size_t); ALIGN(size_t);
    SIZE(void *); ALIGN(void *);
    SIZE(int); ALIGN(int);
    SIZE(tb_status); ALIGN(tb_status);
    SIZE(tb_evidence_kind); ALIGN(tb_evidence_kind);
    SIZE(tb_evidence_v1); ALIGN(tb_evidence_v1);
    FIELD(tb_evidence_v1, kind);
    FIELD(tb_evidence_v1, before_size);
    FIELD(tb_evidence_v1, after_size);
    FIELD(tb_evidence_v1, before_sha256);
    FIELD(tb_evidence_v1, after_sha256);
    FIELD(tb_evidence_v1, deleted_size);
    FIELD(tb_evidence_v1, deleted_offset);
    FIELD(tb_evidence_v1, deleted_sha256);
    SIZE(tb_receipt_v1); ALIGN(tb_receipt_v1);
    FIELD(tb_receipt_v1, evidence);
    FIELD(tb_receipt_v1, has_previous);
    FIELD(tb_receipt_v1, previous_hash);
    FIELD(tb_receipt_v1, receipt_hash);
    METRIC("TB_FINGERPRINT_ABI_VERSION", TB_FINGERPRINT_ABI_VERSION);
    METRIC("TB_EVIDENCE_ABI_VERSION", TB_EVIDENCE_ABI_VERSION);
    METRIC("TB_RECEIPT_ABI_VERSION", TB_RECEIPT_ABI_VERSION);
    METRIC("TB_SHA256_DIGEST_SIZE", TB_SHA256_DIGEST_SIZE);
    METRIC("TB_RECEIPT_JSON_MAX", TB_RECEIPT_JSON_MAX);
    METRIC("TB_EVIDENCE_UNCHANGED", TB_EVIDENCE_UNCHANGED);
    METRIC("TB_EVIDENCE_OBSERVED_TRANSITION", TB_EVIDENCE_OBSERVED_TRANSITION);
    METRIC("TB_EVIDENCE_EXPLICIT_DELETE", TB_EVIDENCE_EXPLICIT_DELETE);
    METRIC("TB_OK", TB_OK);
    METRIC("TB_ERR_ARGUMENT", TB_ERR_ARGUMENT);
    METRIC("TB_ERR_LENGTH", TB_ERR_LENGTH);
    METRIC("TB_ERR_MEMORY", TB_ERR_MEMORY);
    METRIC("TB_ERR_CRYPTO", TB_ERR_CRYPTO);
    METRIC("TB_ERR_STATE", TB_ERR_STATE);
    METRIC("TB_ERR_MISMATCH", TB_ERR_MISMATCH);
    METRIC("TB_ERR_FORMAT", TB_ERR_FORMAT);
    return 0;
}
