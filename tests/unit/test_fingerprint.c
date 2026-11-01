/* SPDX-License-Identifier: Apache-2.0 */
#include "tombstone/fingerprint.h"

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

static void known_answer(const void *data, size_t len, const char *expected)
{
    unsigned char digest[TB_SHA256_DIGEST_SIZE];
    unsigned char digest_streamed[TB_SHA256_DIGEST_SIZE];
    char hex[TB_SHA256_HEX_SIZE];
    tb_sha256_ctx *ctx = NULL;
    const unsigned char *p = (const unsigned char *)data;
    size_t i;

    CHECK(tb_sha256_bytes(data, len, digest) == TB_OK);
    CHECK(tb_sha256_hex(digest, hex) == TB_OK);
    CHECK(strcmp(hex, expected) == 0);
    CHECK(tb_sha256_new(&ctx) == TB_OK);
    CHECK(ctx != NULL);
    CHECK(tb_sha256_update(ctx, NULL, 0) == TB_OK);
    for (i = 0; i < len; ++i) {
        CHECK(tb_sha256_update(ctx, p + i, 1) == TB_OK);
    }
    CHECK(tb_sha256_final(ctx, digest_streamed) == TB_OK);
    CHECK(memcmp(digest, digest_streamed, sizeof(digest)) == 0);
    CHECK(tb_sha256_final(ctx, digest_streamed) == TB_ERR_STATE);
    CHECK(tb_sha256_update(ctx, NULL, 0) == TB_ERR_STATE);
    tb_sha256_free(ctx);
}

static void test_vectors(void)
{
    static const unsigned char binary[] = {0x00, 0xff, 0x80, 0x0a, 0x00, 0x01};
    static const char long_msg[] =
        "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq";
    unsigned char thousand[1000];
    unsigned char digest[TB_SHA256_DIGEST_SIZE];
    char hex[TB_SHA256_HEX_SIZE];
    tb_sha256_ctx *ctx = NULL;
    size_t i;
    CHECK(tb_fingerprint_abi_version() == TB_FINGERPRINT_ABI_VERSION);
    CHECK(TB_SHA256_DIGEST_SIZE == 32u && TB_SHA256_HEX_SIZE == 65u);
    known_answer(NULL, 0, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
    known_answer("abc", 3, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    known_answer(long_msg, sizeof(long_msg) - 1u,
                 "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1");
    known_answer(binary, sizeof(binary), "4c174dac467f0fb0edf9f97920325645e039e095226a96cf25260f45a98fbd17");
    memset(thousand, 'a', sizeof(thousand));
    CHECK(tb_sha256_new(&ctx) == TB_OK);
    for (i = 0; i < 1000u; ++i) {
        CHECK(tb_sha256_update(ctx, thousand, sizeof(thousand)) == TB_OK);
    }
    CHECK(tb_sha256_final(ctx, digest) == TB_OK);
    CHECK(tb_sha256_hex(digest, hex) == TB_OK);
    CHECK(strcmp(hex, "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0") == 0);
    tb_sha256_free(ctx);
}

static void test_errors(void)
{
    unsigned char out[TB_SHA256_DIGEST_SIZE];
    unsigned char before[TB_SHA256_DIGEST_SIZE];
    char hex[TB_SHA256_HEX_SIZE];
    tb_sha256_ctx *ctx = NULL;
    const unsigned char one = 1;
    memset(out, 0xa5, sizeof(out));
    memcpy(before, out, sizeof(out));
    CHECK(tb_sha256_bytes(NULL, 1, out) == TB_ERR_ARGUMENT);
    CHECK(memcmp(out, before, sizeof(out)) == 0);
    CHECK(tb_sha256_bytes(&one, 1, NULL) == TB_ERR_ARGUMENT);
    CHECK(tb_sha256_hex(NULL, hex) == TB_ERR_ARGUMENT);
    CHECK(tb_sha256_hex(before, NULL) == TB_ERR_ARGUMENT);
    CHECK(tb_sha256_new(NULL) == TB_ERR_ARGUMENT);
    CHECK(tb_sha256_update(NULL, NULL, 0) == TB_ERR_ARGUMENT);
    CHECK(tb_sha256_final(NULL, out) == TB_ERR_ARGUMENT);
    CHECK(tb_sha256_new(&ctx) == TB_OK);
    CHECK(tb_sha256_update(ctx, NULL, 1) == TB_ERR_ARGUMENT);
    CHECK(tb_sha256_final(ctx, NULL) == TB_ERR_ARGUMENT);
    CHECK(tb_sha256_update(ctx, &one, 1) == TB_OK);
    CHECK(tb_sha256_final(ctx, out) == TB_OK);
    CHECK(tb_sha256_update(ctx, &one, 1) == TB_ERR_STATE);
    tb_sha256_free(ctx);
    tb_sha256_free(NULL);

#if SIZE_MAX > (UINT64_MAX / UINT64_C(8))
    /* No giant buffer is dereferenced; the length is rejected first. */
    CHECK(tb_sha256_bytes(&one, SIZE_MAX, out) == TB_ERR_LENGTH);
    CHECK(tb_sha256_new(&ctx) == TB_OK);
    CHECK(tb_sha256_update(ctx, &one, SIZE_MAX) == TB_ERR_LENGTH);
    CHECK(tb_sha256_update(ctx, &one, 1) == TB_OK);
    CHECK(tb_sha256_final(ctx, out) == TB_OK);
    tb_sha256_free(ctx);
#endif
}

int main(void)
{
    test_vectors();
    test_errors();
    puts("PASS: C99 SHA-256 NIST vectors, binary data, streaming, ABI, errors and length limits");
    return 0;
}
