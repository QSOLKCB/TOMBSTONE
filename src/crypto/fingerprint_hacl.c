/* SPDX-License-Identifier: Apache-2.0 */
/* Optional SHA-256 backend: exact upstream HACL* generated C (MIT-licensed)
 * under vendor/hacl-star/. The TOMBSTONE adapter itself is NOT formally
 * proved; its ABI, allocator handling and compiler remain explicit premises.
 * The default SHA implementation remains the original OpenSSL provider.
 */
#include "tombstone/fingerprint.h"
#include "Hacl_Hash_SHA2.h"
#include "Hacl_Streaming_Types.h"
#include <limits.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#if CHAR_BIT != 8
#error "TOMBSTONE requires eight-bit bytes"
#endif
#define TB_MAX_SHA256_BYTES (UINT64_MAX / UINT64_C(8))

struct tb_sha256_ctx {
    Hacl_Streaming_MD_state_32 *backend;
    uint64_t total;
    int finished;
    int failed;
};

unsigned int tb_fingerprint_abi_version(void)
{
    return TB_FINGERPRINT_ABI_VERSION;
}

tb_status tb_sha256_new(tb_sha256_ctx **out_ctx)
{
    tb_sha256_ctx *ctx;
    if (out_ctx == NULL) return TB_ERR_ARGUMENT;
    *out_ctx = NULL;
    ctx = (tb_sha256_ctx *)calloc(1u, sizeof(*ctx));
    if (ctx == NULL) return TB_ERR_MEMORY;
    ctx->backend = Hacl_Hash_SHA2_malloc_256();
    if (ctx->backend == NULL) {
        free(ctx);
        return TB_ERR_MEMORY;
    }
    *out_ctx = ctx;
    return TB_OK;
}

tb_status tb_sha256_update(tb_sha256_ctx *ctx, const void *data, size_t length)
{
    const uint8_t *p = (const uint8_t *)data;
    size_t remaining = length;
    if (ctx == NULL) return TB_ERR_ARGUMENT;
    if (ctx->finished || ctx->failed) return TB_ERR_STATE;
    if (length != 0u && data == NULL) return TB_ERR_ARGUMENT;
    if ((uint64_t)length > TB_MAX_SHA256_BYTES - ctx->total) return TB_ERR_LENGTH;
    while (remaining != 0u) {
        uint32_t chunk = remaining > UINT32_MAX ? UINT32_MAX : (uint32_t)remaining;
        Hacl_Streaming_Types_error_code rc =
            Hacl_Hash_SHA2_update_256(ctx->backend, (uint8_t *)p, chunk);
        if (rc != Hacl_Streaming_Types_Success) {
            ctx->failed = 1;
            return rc == Hacl_Streaming_Types_MaximumLengthExceeded ? TB_ERR_LENGTH :
                rc == Hacl_Streaming_Types_OutOfMemory ? TB_ERR_MEMORY : TB_ERR_CRYPTO;
        }
        p += chunk;
        remaining -= chunk;
    }
    ctx->total += (uint64_t)length;
    return TB_OK;
}

tb_status tb_sha256_final(tb_sha256_ctx *ctx,
                          unsigned char out[TB_SHA256_DIGEST_SIZE])
{
    unsigned char digest[TB_SHA256_DIGEST_SIZE];
    if (ctx == NULL || out == NULL) return TB_ERR_ARGUMENT;
    if (ctx->finished || ctx->failed) return TB_ERR_STATE;
    Hacl_Hash_SHA2_digest_256(ctx->backend, digest);
    ctx->finished = 1;
    memcpy(out, digest, sizeof(digest));
    return TB_OK;
}

void tb_sha256_free(tb_sha256_ctx *ctx)
{
    if (ctx != NULL) {
        Hacl_Hash_SHA2_free_256(ctx->backend);
        free(ctx);
    }
}

tb_status tb_sha256_bytes(const void *data, size_t length,
                          unsigned char out[TB_SHA256_DIGEST_SIZE])
{
    tb_sha256_ctx *ctx = NULL;
    tb_status status;
    if (out == NULL || (length != 0u && data == NULL)) return TB_ERR_ARGUMENT;
    if ((uint64_t)length > TB_MAX_SHA256_BYTES) return TB_ERR_LENGTH;
    status = tb_sha256_new(&ctx);
    if (status != TB_OK) return status;
    status = tb_sha256_update(ctx, data, length);
    if (status == TB_OK) status = tb_sha256_final(ctx, out);
    tb_sha256_free(ctx);
    return status;
}

tb_status tb_sha256_hex(const unsigned char digest[TB_SHA256_DIGEST_SIZE],
                        char out[TB_SHA256_HEX_SIZE])
{
    static const char digits[] = "0123456789abcdef";
    size_t i;
    if (digest == NULL || out == NULL) return TB_ERR_ARGUMENT;
    for (i = 0; i < TB_SHA256_DIGEST_SIZE; ++i) {
        out[2u*i] = digits[digest[i] >> 4];
        out[2u*i + 1u] = digits[digest[i] & 0x0fu];
    }
    out[TB_SHA256_HEX_SIZE-1u] = '\0';
    return TB_OK;
}
