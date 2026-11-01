/* SPDX-License-Identifier: Apache-2.0 */
/* Bounded CBMC source-level obligations for the ACTUAL Phase 13 adapter.
 * HACL* operations below are TEST MODELS, not proofs of its algorithm.
 * Model permits allocation failure and nondeterministic update statuses.
 * No claim about real HACL, compiler output or historical deletion follows.
 */
#include "tombstone/fingerprint.h"
#include "Hacl_Hash_SHA2.h"
#include "Hacl_Streaming_Types.h"
#include <stddef.h>
#include <stdint.h>
#include <string.h>

extern unsigned int nondet_uint(void);
extern unsigned char nondet_uchar(void);
void __CPROVER_assume(int);
void __CPROVER_assert(int, const char *);

static union {
    uint64_t align;
    unsigned char bytes[64];
} model_backend;

Hacl_Streaming_MD_state_32 *Hacl_Hash_SHA2_malloc_256(void)
{
    return (nondet_uchar() & 1u) != 0u
        ? NULL : (Hacl_Streaming_MD_state_32 *)(void *)model_backend.bytes;
}

void Hacl_Hash_SHA2_free_256(Hacl_Streaming_MD_state_32 *p)
{
    (void)p;
}

Hacl_Streaming_Types_error_code Hacl_Hash_SHA2_update_256(
    Hacl_Streaming_MD_state_32 *state, uint8_t *input, uint32_t len)
{
    unsigned char status = nondet_uchar();
    (void)state;
    (void)input;
    (void)len;
    __CPROVER_assume(status <= Hacl_Streaming_Types_OutOfMemory);
    return status;
}

void Hacl_Hash_SHA2_digest_256(Hacl_Streaming_MD_state_32 *state, uint8_t *out)
{
    (void)state;
    memset(out, 0x5a, TB_SHA256_DIGEST_SIZE);
}

/* Includes the exact production adapter body, not a reimplementation. */
#include "../../src/crypto/fingerprint_hacl.c"

static int untouched(const unsigned char a[TB_SHA256_DIGEST_SIZE])
{
    unsigned i;
    for (i = 0u; i < TB_SHA256_DIGEST_SIZE; ++i)
        if (a[i] != 0xa5) return 0;
    return 1;
}

void check_one_shot(void)
{
    unsigned char input[4], digest[TB_SHA256_DIGEST_SIZE];
    size_t len = nondet_uint();
    tb_status rc;
    unsigned i;
    __CPROVER_assume(len <= 4u);
    for (i = 0u; i < 4u; ++i) input[i] = nondet_uchar();
    memset(digest, 0xa5, sizeof(digest));
    rc = tb_sha256_bytes(input, len, digest);
    __CPROVER_assert(rc == TB_OK || rc == TB_ERR_MEMORY ||
        rc == TB_ERR_LENGTH || rc == TB_ERR_CRYPTO,
        "all bounded provider paths map to public status codes");
    if (rc != TB_OK)
        __CPROVER_assert(untouched(digest),
            "one-shot error never modifies caller digest");
    else
        for (i = 0u; i < TB_SHA256_DIGEST_SIZE; ++i)
            __CPROVER_assert(digest[i] == 0x5a,
                "success writes exactly the modeled digest");
}

void check_stream(void)
{
    unsigned char input[4], digest[TB_SHA256_DIGEST_SIZE];
    size_t len = nondet_uint();
    tb_sha256_ctx *ctx = NULL;
    tb_status init, updated, finished;
    unsigned i;
    __CPROVER_assume(len <= 4u);
    for (i = 0u; i < 4u; ++i) input[i] = nondet_uchar();
    memset(digest, 0xa5, sizeof(digest));
    init = tb_sha256_new(&ctx);
    if (init != TB_OK) {
        __CPROVER_assert(init == TB_ERR_MEMORY && ctx == NULL,
            "all initialization failures zero the output context");
        return;
    }
    __CPROVER_assert(ctx != NULL, "success initializes a non-null context");
    updated = tb_sha256_update(ctx, input, len);
    if (updated == TB_OK) {
        finished = tb_sha256_final(ctx, digest);
        __CPROVER_assert(finished == TB_OK,
            "the non-failing modeled provider allows finalization");
    } else {
        finished = tb_sha256_final(ctx, digest);
        __CPROVER_assert(finished == TB_ERR_STATE,
            "provider failures poison streaming state");
        __CPROVER_assert(untouched(digest), "failed stream leaves digest untouched");
    }
    tb_sha256_free(ctx);
}

void check_invalid(void)
{
    unsigned char digest[TB_SHA256_DIGEST_SIZE];
    unsigned char input[1] = {0x22};
    tb_sha256_ctx *ctx = NULL;
    tb_status rc;
    memset(digest, 0xa5, sizeof(digest));
    __CPROVER_assert(tb_sha256_bytes(NULL, 1u, digest) == TB_ERR_ARGUMENT,
        "null positive-length input rejected");
    __CPROVER_assert(untouched(digest), "argument rejection does not write");
    rc = tb_sha256_new(&ctx);
    if (rc == TB_OK) {
        __CPROVER_assert(tb_sha256_update(ctx, NULL, 1u) == TB_ERR_ARGUMENT,
            "null positive-length streaming input rejected");
        __CPROVER_assert(tb_sha256_update(ctx, input, 0u) == TB_OK,
            "zero length update is a no-op");
        tb_sha256_free(ctx);
    } else {
        __CPROVER_assert(rc == TB_ERR_MEMORY && ctx == NULL,
            "allocation failure is the only initialization error");
    }
}
