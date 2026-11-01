/* SPDX-License-Identifier: Apache-2.0 */
/* Build a separate translation unit against the installed-style public header. */
#include "tombstone/fingerprint.h"
#include <stdio.h>
#include <string.h>

int main(void)
{
    static const unsigned char payload[] = {0, 1, 2, 3, 255, 128};
    unsigned char digest[TB_SHA256_DIGEST_SIZE];
    char hex[TB_SHA256_HEX_SIZE];
    if (tb_sha256_bytes(payload, sizeof(payload), digest) != TB_OK ||
        tb_sha256_hex(digest, hex) != TB_OK ||
        strlen(hex) != 64u) {
        fputs("FAIL: public ABI integration\n", stderr);
        return 1;
    }
    puts("PASS: standalone C99 consumer links libtombstone.a and hashes binary data");
    return 0;
}
