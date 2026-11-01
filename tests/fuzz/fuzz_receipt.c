/* SPDX-License-Identifier: Apache-2.0 */
/* LLVM libFuzzer: strict schema-limited receipt parser. */
#include "tombstone/receipt.h"
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#define REQUIRE(x) do { if (!(x)) abort(); } while (0)
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t len)
{
    tb_receipt_v1 out, before, decoded, rebuilt;
    char json[TB_RECEIPT_JSON_MAX];
    size_t written = 0u;
    tb_status st;
    if (len > 16384u) return 0;
    memset(&out, 0xa5, sizeof(out));
    before = out;
    st = tb_receipt_parse((const char *)data, len, &out);
    if (st != TB_OK) {
        REQUIRE(st == TB_ERR_FORMAT || st == TB_ERR_MISMATCH || st == TB_ERR_LENGTH);
        REQUIRE(memcmp(&out, &before, sizeof(out)) == 0);
        return 0;
    }
    REQUIRE(tb_receipt_encode(&out, json, sizeof(json), &written) == TB_OK);
    REQUIRE(written > 0u && written < sizeof(json));
    REQUIRE(tb_receipt_parse(json, written, &decoded) == TB_OK);
    REQUIRE(memcmp(decoded.receipt_hash, out.receipt_hash, 32u) == 0);
    REQUIRE(decoded.evidence.kind == out.evidence.kind);
    REQUIRE(decoded.has_previous == out.has_previous);
    REQUIRE(tb_receipt_create(&out.evidence,
                out.has_previous ? out.previous_hash : NULL, &rebuilt) == TB_OK);
    REQUIRE(memcmp(rebuilt.receipt_hash, out.receipt_hash, 32u) == 0);
    if (!out.has_previous)
        REQUIRE(tb_receipt_verify_chain(&out, 1u, NULL) == TB_OK);
    return 0;
}
