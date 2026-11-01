/* SPDX-License-Identifier: Apache-2.0 */
#include "tombstone/deletion.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(expr) do { \
    if (!(expr)) { \
        fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #expr); \
        exit(1); \
    } \
} while (0)

static void equal_digest(const void *data, size_t len,
                         const unsigned char actual[TB_SHA256_DIGEST_SIZE])
{
    unsigned char expected[TB_SHA256_DIGEST_SIZE];
    CHECK(tb_sha256_bytes(data, len, expected) == TB_OK);
    CHECK(memcmp(actual, expected, sizeof(expected)) == 0);
}

static void expect_failure(tb_status result, tb_status want,
                           const tb_evidence_v1 *actual,
                           const tb_evidence_v1 *sentinel)
{
    CHECK(result == want);
    CHECK(memcmp(actual, sentinel, sizeof(*actual)) == 0);
}

static void observed_cases(void)
{
    static const unsigned char old[] = {'A', 0, 255, 'B', 0x80};
    static const unsigned char same[] = {'A', 0, 255, 'B', 0x80};
    static const unsigned char changed[] = {'A', 0, 254, 'B', 0x80};
    tb_evidence_v1 ev, guard;
    CHECK(tb_evidence_abi_version() == TB_EVIDENCE_ABI_VERSION);
    memset(&ev, 0x5a, sizeof(ev));
    CHECK(tb_observe_transition(old, sizeof(old), same, sizeof(same), &ev) == TB_OK);
    CHECK(ev.kind == TB_EVIDENCE_UNCHANGED);
    CHECK(ev.before_size == sizeof(old) && ev.after_size == sizeof(same));
    equal_digest(old, sizeof(old), ev.before_sha256);
    equal_digest(same, sizeof(same), ev.after_sha256);
    CHECK(ev.deleted_size == 0u && ev.deleted_offset == 0u);
    CHECK(memcmp(ev.deleted_sha256, (unsigned char[TB_SHA256_DIGEST_SIZE]){0},
                 TB_SHA256_DIGEST_SIZE) == 0);

    CHECK(tb_observe_transition(old, sizeof(old), changed, sizeof(changed), &ev) == TB_OK);
    CHECK(ev.kind == TB_EVIDENCE_OBSERVED_TRANSITION);
    CHECK(ev.deleted_size == 0u);
    CHECK(ev.before_size == ev.after_size);
    equal_digest(changed, sizeof(changed), ev.after_sha256);

    CHECK(tb_observe_transition(NULL, 0u, NULL, 0u, &ev) == TB_OK);
    CHECK(ev.kind == TB_EVIDENCE_UNCHANGED);
    equal_digest(NULL, 0u, ev.before_sha256);
    CHECK(tb_observe_transition(NULL, 0u, old, sizeof(old), &ev) == TB_OK);
    CHECK(ev.kind == TB_EVIDENCE_OBSERVED_TRANSITION);
    CHECK(tb_observe_transition(old, sizeof(old), NULL, 0u, &ev) == TB_OK);
    CHECK(ev.kind == TB_EVIDENCE_OBSERVED_TRANSITION);
    CHECK(ev.deleted_size == 0u); /* Empty after does NOT infer deletion. */

    memset(&ev, 0x5a, sizeof(ev)); guard = ev;
    expect_failure(tb_observe_transition(NULL, 1u, old, sizeof(old), &ev),
                   TB_ERR_ARGUMENT, &ev, &guard);
    expect_failure(tb_observe_transition(old, sizeof(old), NULL, 1u, &ev),
                   TB_ERR_ARGUMENT, &ev, &guard);
    expect_failure(tb_observe_transition(old, sizeof(old), old, sizeof(old), NULL),
                   TB_ERR_ARGUMENT, &ev, &guard);
#if SIZE_MAX > TB_EVIDENCE_MAX_BYTES
    expect_failure(tb_observe_transition(old, SIZE_MAX, old, sizeof(old), &ev),
                   TB_ERR_LENGTH, &ev, &guard);
    expect_failure(tb_observe_transition(old, sizeof(old), old, SIZE_MAX, &ev),
                   TB_ERR_LENGTH, &ev, &guard);
#endif
}

static void verified_splices(void)
{
    static const unsigned char before[] = {'1',' ','2',' ','3',' ','4',' ','5'};
    static const unsigned char removed[] = {'3',' ','4',' '};
    static const unsigned char after[] = {'1',' ','2',' ','5'};
    static const unsigned char binary[] = {0, 255, 1, 0, 0x80, 2};
    static const unsigned char binary_after[] = {0, 255, 0x80, 2};
    static const unsigned char binary_removed[] = {1, 0};
    static const unsigned char repeated[] = {'a','a','a','a'};
    static const unsigned char shorter[] = {'a','a','a'};
    static const unsigned char initial[] = {'x', 'y'};
    static const unsigned char tail[] = {'z'};
    static const unsigned char replacement[] = {'x', 'z'};
    tb_evidence_v1 ev;
    unsigned char before_copy[sizeof(before)];
    memcpy(before_copy, before, sizeof(before));

    CHECK(tb_witness_delete(before, sizeof(before), removed, sizeof(removed), 4u,
                            after, sizeof(after), &ev) == TB_OK);
    CHECK(ev.kind == TB_EVIDENCE_EXPLICIT_DELETE);
    CHECK(ev.before_size == 9u && ev.after_size == 5u);
    CHECK(ev.deleted_offset == 4u && ev.deleted_size == 4u);
    equal_digest(before, sizeof(before), ev.before_sha256);
    equal_digest(after, sizeof(after), ev.after_sha256);
    equal_digest(removed, sizeof(removed), ev.deleted_sha256);
    CHECK(memcmp(before, before_copy, sizeof(before)) == 0);

    CHECK(tb_witness_delete(binary, sizeof(binary), binary_removed,
                            sizeof(binary_removed), 2u, binary_after,
                            sizeof(binary_after), &ev) == TB_OK);
    CHECK(ev.deleted_offset == 2u);
    equal_digest(binary_removed, sizeof(binary_removed), ev.deleted_sha256);

    CHECK(tb_witness_delete(repeated, sizeof(repeated), "a", 1u, 0u,
                            shorter, sizeof(shorter), &ev) == TB_OK);
    CHECK(ev.deleted_offset == 0u);
    CHECK(tb_witness_delete(repeated, sizeof(repeated), "a", 1u, 3u,
                            shorter, sizeof(shorter), &ev) == TB_OK);
    CHECK(ev.deleted_offset == 3u); /* Claimed offset, not inferred identity. */

    CHECK(tb_witness_delete(initial, sizeof(initial), "x", 1u, 0u,
                            "y", 1u, &ev) == TB_OK);
    CHECK(tb_witness_delete(initial, sizeof(initial), "xy", 2u, 0u,
                            NULL, 0u, &ev) == TB_OK);
    CHECK(ev.deleted_size == 2u && ev.after_size == 0u);
    equal_digest(NULL, 0u, ev.after_sha256);
    CHECK(tb_witness_delete(tail, sizeof(tail), tail, sizeof(tail), 0u,
                            NULL, 0u, &ev) == TB_OK);
    CHECK(tb_witness_delete(initial, sizeof(initial), "y", 1u, 1u,
                            "x", 1u, &ev) == TB_OK);

    /* Replacement is an observed transition, never an explicit deletion. */
    CHECK(tb_observe_transition(initial, sizeof(initial), replacement,
                                sizeof(replacement), &ev) == TB_OK);
    CHECK(ev.kind == TB_EVIDENCE_OBSERVED_TRANSITION);
    CHECK(ev.deleted_size == 0u);
}

static void rejected_splices(void)
{
    static const unsigned char before[] = {'a', 0, 'b', 0, 'c'};
    static const unsigned char removed[] = {0, 'b'};
    static const unsigned char after[] = {'a', 0, 'c'};
    static const unsigned char wrong_after[] = {'a', 'x', 'c'};
    static const unsigned char wrong_removed[] = {0, 'x'};
    tb_evidence_v1 ev, sentinel;
    memset(&ev, 0xa5, sizeof(ev));
    sentinel = ev;
#define BAD(code, b, bn, r, rn, off, a, an) \
    expect_failure(tb_witness_delete((b), (bn), (r), (rn), (off), (a), (an), &ev), \
                   (code), &ev, &sentinel)
    BAD(TB_ERR_MISMATCH, before, sizeof(before), removed, sizeof(removed),
        1u, wrong_after, sizeof(wrong_after));
    BAD(TB_ERR_MISMATCH, before, sizeof(before), wrong_removed, sizeof(wrong_removed),
        1u, after, sizeof(after));
    BAD(TB_ERR_MISMATCH, before, sizeof(before), removed, sizeof(removed),
        0u, after, sizeof(after));
    BAD(TB_ERR_MISMATCH, before, sizeof(before), removed, sizeof(removed),
        1u, after, sizeof(after)-1u);
    BAD(TB_ERR_ARGUMENT, before, sizeof(before), removed, 0u,
        1u, after, sizeof(after));
    BAD(TB_ERR_ARGUMENT, NULL, sizeof(before), removed, sizeof(removed),
        1u, after, sizeof(after));
    BAD(TB_ERR_ARGUMENT, before, sizeof(before), NULL, sizeof(removed),
        1u, after, sizeof(after));
    BAD(TB_ERR_ARGUMENT, before, sizeof(before), removed, sizeof(removed),
        1u, NULL, sizeof(after));
    BAD(TB_ERR_LENGTH, before, sizeof(before), removed, sizeof(removed),
        SIZE_MAX, after, sizeof(after));
    BAD(TB_ERR_LENGTH, before, sizeof(before), removed, sizeof(before)+1u,
        0u, after, sizeof(after));
    BAD(TB_ERR_LENGTH, before, 0u, removed, sizeof(removed),
        0u, after, sizeof(after));
#if SIZE_MAX > TB_EVIDENCE_MAX_BYTES
    BAD(TB_ERR_LENGTH, before, SIZE_MAX, removed, sizeof(removed),
        1u, after, sizeof(after));
    BAD(TB_ERR_LENGTH, before, sizeof(before), removed, SIZE_MAX,
        1u, after, sizeof(after));
    BAD(TB_ERR_LENGTH, before, sizeof(before), removed, sizeof(removed),
        1u, after, SIZE_MAX);
#endif
    CHECK(tb_witness_delete(before, sizeof(before), removed, sizeof(removed),
                            1u, after, sizeof(after), NULL) == TB_ERR_ARGUMENT);
    CHECK(memcmp(&ev, &sentinel, sizeof(ev)) == 0);
#undef BAD
}

int main(void)
{
    observed_cases();
    verified_splices();
    rejected_splices();
    puts("PASS: Phase 2 C99 witnessed splices, binary data, no-op, ambiguity and adversarial cases");
    return 0;
}
