/* SPDX-License-Identifier: Apache-2.0 */
/* Phase 17: real C99 receipt-chain, anchored/unanchored negative controls.
 * This is runtime evidence for the historical v1 fixture data. It is not a
 * proof of arbitrary SHA-256, independent custody or historical deletion.
 */
#include "tombstone/receipt.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
  fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #x); exit(1); \
} } while (0)

static size_t load(const char *name, char out[2048])
{
    char path[160];
    FILE *f;
    size_t n;
    int k = snprintf(path, sizeof(path), "machine/examples/%s", name);
    REQUIRE(k > 0 && (size_t)k < sizeof(path));
    f = fopen(path, "rb");
    REQUIRE(f != NULL);
    n = fread(out, 1, 2048u, f);
    REQUIRE(n > 0u && n < 2048u && !ferror(f) && feof(f));
    REQUIRE(fclose(f) == 0);
    return n;
}

static void expect_unchanged(const tb_receipt_v1 *receipts, size_t count,
                             const unsigned char *head, tb_status expected)
{
    tb_receipt_v1 copy[3];
    size_t bytes;
    REQUIRE(count <= 3u);
    bytes = count * sizeof(*receipts);
    if (count != 0u) memcpy(copy, receipts, bytes);
    REQUIRE(tb_receipt_verify_chain(receipts, count, head) == expected);
    if (count != 0u) REQUIRE(memcmp(copy, receipts, bytes) == 0);
}

int main(void)
{
    static const char *const names[] = {
        "explicit-delete-v1.json", "observed-transition-v1.json",
        "unchanged-v1.json"
    };
    static const unsigned int permutations[][3] = {
        {0, 1, 2}, {0, 2, 1}, {1, 0, 2}, {1, 2, 0},
        {2, 0, 1}, {2, 1, 0}
    };
    char json[2048];
    tb_receipt_v1 original[3], candidate[3], forged, modified;
    tb_evidence_v1 evidence;
    size_t i,j,n;

    for (i=0u; i<3u; ++i) {
        n=load(names[i],json);
        REQUIRE(tb_receipt_parse(json,n,&original[i]) == TB_OK);
    }
    expect_unchanged(original, 0u, NULL, TB_ERR_ARGUMENT);
    REQUIRE(tb_receipt_verify_chain(NULL, 3u, NULL) == TB_ERR_ARGUMENT);
    REQUIRE(tb_receipt_verify_chain(original, SIZE_MAX, NULL) == TB_ERR_ARGUMENT);

    for (i=1u; i<=3u; ++i) {
        expect_unchanged(original, i, NULL, TB_OK);
        expect_unchanged(original, i, original[i-1u].receipt_hash, TB_OK);
        expect_unchanged(original, i, original[(i+1u)%3u].receipt_hash,
                         TB_ERR_MISMATCH);
    }

    /* Enumerate all six possible orders, including the one original chain. */
    for (i=0u; i<sizeof(permutations)/sizeof(permutations[0]); ++i) {
        for (j=0u;j<3u;++j) candidate[j]=original[permutations[i][j]];
        expect_unchanged(candidate, 3u, NULL, i==0u ? TB_OK : TB_ERR_MISMATCH);
        expect_unchanged(candidate, 3u, original[2].receipt_hash,
                         i==0u ? TB_OK : TB_ERR_MISMATCH);
    }

    for (i=0u; i<3u; ++i) {
        memcpy(candidate, original, sizeof(candidate));
        candidate[i].receipt_hash[0] ^= 1u;
        expect_unchanged(candidate, 3u, NULL, TB_ERR_MISMATCH);
        memcpy(candidate, original, sizeof(candidate));
        candidate[i].has_previous = (i==0u) ? 1 : 0;
        expect_unchanged(candidate, 3u, NULL, TB_ERR_MISMATCH);
        if (i>0u) {
            memcpy(candidate, original, sizeof(candidate));
            candidate[i].previous_hash[0] ^= 1u;
            expect_unchanged(candidate, 3u, NULL, TB_ERR_MISMATCH);
        }
    }

    candidate[0]=original[0]; candidate[1]=original[2];
    expect_unchanged(candidate,2u,NULL,TB_ERR_MISMATCH);
    candidate[0]=original[1];
    expect_unchanged(candidate,1u,NULL,TB_ERR_MISMATCH);
    candidate[0]=original[2];
    expect_unchanged(candidate,1u,NULL,TB_ERR_MISMATCH);

    /* Well-formed "has_previous" representation is enforced by the actual
     * digest path. Nonzero but invalid 2 in a successor is NOT treated as
     * a validated predecessor state. */
    memcpy(candidate,original,sizeof(candidate));
    candidate[1].has_previous=2;
    expect_unchanged(candidate,3u,NULL,TB_ERR_FORMAT);
    modified=original[0]; modified.previous_hash[0] = 1u;
    expect_unchanged(&modified,1u,NULL,TB_ERR_FORMAT);

    /* A separately generated coherent genesis can validate locally, but
     * cannot match the previously retained head of the historical fixtures. */
    REQUIRE(tb_observe_transition("x",1u,"y",1u,&evidence)==TB_OK);
    REQUIRE(tb_receipt_create(&evidence,NULL,&forged)==TB_OK);
    expect_unchanged(&forged,1u,NULL,TB_OK);
    expect_unchanged(&forged,1u,original[2].receipt_hash,TB_ERR_MISMATCH);

    puts("PASS: actual C99 chain genesis, 6 permutations, prefixes, links, tampered hashes and retained head");
    puts("LIMIT: bounded runtime fixture replay cannot establish universal crypto, timestamp or erasure proof");
    return 0;
}
