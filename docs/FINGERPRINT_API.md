# C99 fingerprint API — Phase 1

**Implemented:** binary-safe SHA-256 operations via OpenSSL EVP and a public C ABI. **Not implemented:** deletion witnessing, receipts, filesystem hashes, or a user CLI.

## Public API

\`include/tombstone/fingerprint.h\` exports:

- \`tb_fingerprint_abi_version(void)\`: returns \`TB_FINGERPRINT_ABI_VERSION\` (currently 1).
- \`tb_sha256_bytes(data, length, out)\`: one-shot SHA-256 of exactly \`length\` bytes.
- \`tb_sha256_new(&ctx)\`, \`tb_sha256_update(ctx, data, length)\`, \`tb_sha256_final(ctx, out)\`, \`tb_sha256_free(ctx)\`: incremental mode.
- \`tb_sha256_hex(digest, hex)\`: lowercase 64-character hex plus terminating NUL.

Status results are \`TB_OK\`, \`TB_ERR_ARGUMENT\`, \`TB_ERR_LENGTH\`, \`TB_ERR_MEMORY\`, \`TB_ERR_CRYPTO\` and \`TB_ERR_STATE\`. A successful output digest is **32 bytes**. A hex destination must accommodate **65 bytes**.

## Minimal example

\`\`\`c
#include "tombstone/fingerprint.h"
#include <stdio.h>

int main(void) {
    const unsigned char bytes[] = {0, 255, 10};
    unsigned char digest[TB_SHA256_DIGEST_SIZE];
    char hex[TB_SHA256_HEX_SIZE];
    if (tb_sha256_bytes(bytes, sizeof bytes, digest) != TB_OK ||
        tb_sha256_hex(digest, hex) != TB_OK) return 1;
    puts(hex);
    return 0;
}
\`\`\`

After \`make\`, compile a consumer using:

\`\`\`sh
cc -std=c99 -Iinclude example.c build/libtombstone.a $(pkg-config --libs openssl) -o example
\`\`\`

## Memory and error contract

- All input buffers are binary, length-delimited and borrowed only during each call; no hidden copy is retained by TOMBSTONE after the hashing operation. The OpenSSL hashing context retains its internal digest state until freed.
- Null \`data\` is allowed **only** for \`length == 0\`. Null output pointers are errors. Outputs must have the specified capacity and may not overlap inputs.
- For the one-shot operation and \`final\`, an error does not modify the digest output.
- An incremental context must be released with \`tb_sha256_free\`, whether or not an earlier operation failed. Freeing \`NULL\` is allowed.
- \`final\` consumes the state; a second final or an update afterward returns \`TB_ERR_STATE\`. Contexts are **not** concurrently shareable.
- SHA-256 has a 64-bit bit count: the core rejects total input lengths above \`UINT64_MAX / 8\`, before accessing an overlarge caller-provided buffer where detectable.
- The caller is responsible for buffer validity and correct capacity; C99 cannot validate arbitrary pointers.
- The core does not operate on files, log, store data, perform telemetry or perform any deletion. A hash of a guessable secret is not secret.

## Backend and portability

The code uses OpenSSL's **EVP** digest API (\`EVP_sha256\`, \`EVP_DigestInit_ex\`, \`EVP_DigestUpdate\`, \`EVP_DigestFinal_ex\`). OpenSSL is a system dependency rather than included cryptographic code. GCC and Clang are verified in Linux CI; GNU \`ar rcsD\` makes deterministic static archives. The runtime digest itself is independent of compiler or host for the same input bytes.

See [ROADMAP](../ROADMAP.md) for future explicit-deletion and receipt layers.
