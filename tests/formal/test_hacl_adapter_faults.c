/* SPDX-License-Identifier: Apache-2.0 */
/* Phase 13: actual HACL-backed C99 adapter; test-only GNU ld --wrap faults.
 * Only the HACL and allocator calls are intercepted; never built in production.
 */
#include "tombstone/fingerprint.h"
#include "Hacl_Hash_SHA2.h"
#include "Hacl_Streaming_Types.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { fprintf(stderr, "FAIL %s:%d: %s\\n", __FILE__, __LINE__, #x); exit(1); } } while (0)

static unsigned allocations;
static unsigned fail_at;
static Hacl_Streaming_Types_error_code update_fault;

void *__real_calloc(size_t n, size_t z);
void *__real_malloc(size_t n);
Hacl_Streaming_Types_error_code __real_Hacl_Hash_SHA2_update_256(
    Hacl_Streaming_MD_state_32 *, uint8_t *, uint32_t);

void *__wrap_calloc(size_t n, size_t z)
{
    ++allocations;
    if (fail_at && allocations == fail_at) return NULL;
    return __real_calloc(n, z);
}

void *__wrap_malloc(size_t n)
{
    ++allocations;
    if (fail_at && allocations == fail_at) return NULL;
    return __real_malloc(n);
}

Hacl_Streaming_Types_error_code __wrap_Hacl_Hash_SHA2_update_256(
    Hacl_Streaming_MD_state_32 *state, uint8_t *input, uint32_t length)
{
    if (update_fault != Hacl_Streaming_Types_Success) return update_fault;
    return __real_Hacl_Hash_SHA2_update_256(state, input, length);
}

static void test_allocation_faults(void)
{
    unsigned n;
    const unsigned char data[] = {'a', 0, 'b'};
    unsigned char digest[TB_SHA256_DIGEST_SIZE];
    for (n = 1u; n <= 4u; ++n) {
        tb_sha256_ctx *ctx = (tb_sha256_ctx *)(uintptr_t)1u;
        allocations = 0u;
        fail_at = n;
        CHECK(tb_sha256_new(&ctx) == TB_ERR_MEMORY);
        CHECK(ctx == NULL);
        CHECK(allocations == n);
        fail_at = 0u;
    }
    allocations = 0u;
    fail_at = 1u;
    memset(digest, 0xa5, sizeof(digest));
    CHECK(tb_sha256_bytes(data, sizeof(data), digest) == TB_ERR_MEMORY);
    for (n = 0u; n < sizeof(digest); ++n) CHECK(digest[n] == 0xa5);
    fail_at = 0u;
}

static void test_update_fault(Hacl_Streaming_Types_error_code error, tb_status expected)
{
    tb_sha256_ctx *ctx = NULL;
    unsigned char digest[TB_SHA256_DIGEST_SIZE];
    const unsigned char data[] = {0x00, 0xff, 0x80};
    size_t i;
    CHECK(tb_sha256_new(&ctx) == TB_OK);
    memset(digest, 0xa5, sizeof(digest));
    update_fault = error;
    CHECK(tb_sha256_update(ctx, data, sizeof(data)) == expected);
    update_fault = Hacl_Streaming_Types_Success;
    CHECK(tb_sha256_update(ctx, data, sizeof(data)) == TB_ERR_STATE);
    CHECK(tb_sha256_final(ctx, digest) == TB_ERR_STATE);
    for (i = 0u; i < sizeof(digest); ++i) CHECK(digest[i] == 0xa5);
    tb_sha256_free(ctx);

    memset(digest, 0xa5, sizeof(digest));
    update_fault = error;
    CHECK(tb_sha256_bytes(data, sizeof(data), digest) == expected);
    update_fault = Hacl_Streaming_Types_Success;
    for (i = 0u; i < sizeof(digest); ++i) CHECK(digest[i] == 0xa5);
}

static void test_chunk_edges(void)
{
    static const size_t lens[] = {0u, 1u, 55u, 56u, 63u, 64u, 65u, 127u, 128u, 129u, 1024u};
    unsigned char data[1024], expected[32], actual[32];
    size_t i, j, step;
    for (i = 0; i < sizeof(data); ++i) data[i] = (unsigned char)(i * 13u + 1u);
    for (i = 0; i < sizeof(lens)/sizeof(lens[0]); ++i) {
        CHECK(tb_sha256_bytes(data, lens[i], expected) == TB_OK);
        for (step = 1u; step < 18u; step += 4u) {
            tb_sha256_ctx *ctx = NULL;
            CHECK(tb_sha256_new(&ctx) == TB_OK);
            for (j = 0u; j < lens[i]; ) {
                size_t n = lens[i] - j < step ? lens[i] - j : step;
                CHECK(tb_sha256_update(ctx, data + j, n) == TB_OK);
                j += n;
            }
            CHECK(tb_sha256_update(ctx, NULL, 0) == TB_OK);
            CHECK(tb_sha256_final(ctx, actual) == TB_OK);
            CHECK(memcmp(actual, expected, sizeof(actual)) == 0);
            tb_sha256_free(ctx);
        }
    }
}

int main(void)
{
    test_allocation_faults();
    test_update_fault(Hacl_Streaming_Types_MaximumLengthExceeded, TB_ERR_LENGTH);
    test_update_fault(Hacl_Streaming_Types_InvalidAlgorithm, TB_ERR_CRYPTO);
    test_chunk_edges();
    puts("PASS: HACL adapter allocation faults, error-state immutability and SHA padding edges");
    puts("LIMIT: injected executions are not unbounded proof of adapter or provider");
    return 0;
}
