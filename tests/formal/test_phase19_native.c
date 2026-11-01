/* SPDX-License-Identifier: Apache-2.0 */
/* Phase 19 real-source helper tests. Real OpenSSL is linked, no hash stub.
 * This is execution evidence, not a universal libc/SHA or proof theorem.
 */
#include "tombstone/receipt.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../../src/encoding/receipt.c"
#define CHECK(p) do { if(!(p)){ fprintf(stderr,"FAIL %s:%d\n",__FILE__,__LINE__);exit(1);} }while(0)

int main(void)
{
    unsigned char a[32] = {0}, b[32] = {0}, before[32], after[32];
    tb_evidence_v1 evidence={0};
    tb_receipt_v1 receipt={0};
    size_t i;
    CHECK(equal32(a,b)==1);
    for(i=0;i<32u;++i) {
        b[i]=(unsigned char)(i+1u);
        memcpy(before,a,sizeof(a));
        memcpy(after,b,sizeof(b));
        CHECK(equal32(a,b)==0);
        CHECK(memcmp(a,before,sizeof(a))==0);
        CHECK(memcmp(b,after,sizeof(b))==0);
        b[i]=0u;
    }
    CHECK(equal32(a,b)==1);
    evidence.kind=TB_EVIDENCE_UNCHANGED;
    evidence.before_size=0u;
    evidence.after_size=0u;
    receipt.evidence=evidence;
    memset(before,0xa5,sizeof(before));
    CHECK(calculate_hash(&receipt,before)==TB_OK);
    CHECK(memcmp(before,a,sizeof(a))!=0);
    receipt.has_previous=2;
    memset(before,0x5a,sizeof(before));
    CHECK(calculate_hash(&receipt,before)==TB_ERR_FORMAT);
    for(i=0;i<32u;++i) CHECK(before[i]==0x5a);
    puts("PASS: actual equal32 32-position comparisons, read-only inputs, real SHA calculation and invalid-receipt no-write");
    puts("LIMIT: native cases do not prove libc memcmp, SHA provider or arbitrary runtime states");
    return 0;
}
