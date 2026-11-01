/* SPDX-License-Identifier: Apache-2.0 */
#include "tombstone/receipt.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { \
  fprintf(stderr,"FAIL %s:%d: %s\n",__FILE__,__LINE__,#x); exit(1); \
} } while (0)

static void check_hex(const unsigned char d[32],const char *expected)
{
    char hex[TB_SHA256_HEX_SIZE];
    CHECK(tb_sha256_hex(d,hex)==TB_OK);
    CHECK(strcmp(hex,expected)==0);
}
static size_t fixture(const char *name,char *out,size_t cap)
{
    char path[256];
    FILE *fp;
    size_t n;
    CHECK(snprintf(path,sizeof(path),"machine/examples/%s",name)>0);
    fp=fopen(path,"rb");
    CHECK(fp!=NULL);
    n=fread(out,1,cap,fp);
    CHECK(!ferror(fp) && n<cap && feof(fp));
    CHECK(fclose(fp)==0);
    return n;
}
static void bad(const char *json,size_t n,tb_status want)
{
    tb_receipt_v1 out,original;
    memset(&out,0xa5,sizeof(out));
    original=out;
    CHECK(tb_receipt_parse(json,n,&out)==want);
    CHECK(memcmp(&out,&original,sizeof(out))==0);
}
int main(void)
{
    static const char *names[3]={
        "explicit-delete-v1.json",
        "observed-transition-v1.json",
        "unchanged-v1.json"
    };
    static const char *hashes[3]={
        "3917b3dc420ddb728616ee3834867664a7012aa5a4c127e56c65651f1ac4dbde",
        "ba68ca51013bb7a475b2d9991cf59607a1c75dfe34e73a4d1ed9a515a8d02914",
        "84c0b5f9e478c284553822fb95fe31a72ce71a35070e963d67c328fb777f25e6"
    };
    const char *before="1 2 3 4 5", *after="1 2 5", *removed="3 4 ";
    tb_receipt_v1 generated[3],parsed[3],tmp;
    tb_evidence_v1 evidence;
    char fixture_json[2048],canonical[TB_RECEIPT_JSON_MAX],modified[2048];
    size_t n,i,written;
    CHECK(tb_receipt_abi_version()==TB_RECEIPT_ABI_VERSION);
    CHECK(tb_witness_delete(before,9,removed,4,4,after,5,&evidence)==TB_OK);
    CHECK(tb_receipt_create(&evidence,NULL,&generated[0])==TB_OK);
    CHECK(tb_observe_transition(before,9,after,5,&evidence)==TB_OK);
    CHECK(tb_receipt_create(&evidence,generated[0].receipt_hash,&generated[1])==TB_OK);
    CHECK(tb_observe_transition(after,5,after,5,&evidence)==TB_OK);
    CHECK(tb_receipt_create(&evidence,generated[1].receipt_hash,&generated[2])==TB_OK);

    for(i=0;i<3u;++i) {
        check_hex(generated[i].receipt_hash,hashes[i]); /* independent Python vector */
        CHECK(tb_receipt_encode(&generated[i],canonical,sizeof(canonical),&written)==TB_OK);
        CHECK(canonical[0]=='{' && canonical[written-1u]=='}');
        CHECK(tb_receipt_parse(canonical,written,&tmp)==TB_OK);
        CHECK(memcmp(tmp.receipt_hash,generated[i].receipt_hash,32)==0);
        n=fixture(names[i],fixture_json,sizeof(fixture_json));
        CHECK(tb_receipt_parse(fixture_json,n,&parsed[i])==TB_OK);
        CHECK(memcmp(parsed[i].receipt_hash,generated[i].receipt_hash,32)==0);
    }
    CHECK(tb_receipt_verify_chain(parsed,3,NULL)==TB_OK);
    CHECK(tb_receipt_verify_chain(generated,3,generated[2].receipt_hash)==TB_OK);
    CHECK(tb_receipt_verify_chain(generated,3,generated[1].receipt_hash)==TB_ERR_MISMATCH);
    CHECK(tb_receipt_verify_chain(generated,0,NULL)==TB_ERR_ARGUMENT);
    CHECK(tb_receipt_verify_chain(NULL,3,NULL)==TB_ERR_ARGUMENT);

    tmp=generated[0];tmp.receipt_hash[0]^=1u;
    CHECK(tb_receipt_verify_chain(&tmp,1,NULL)==TB_ERR_MISMATCH);
    tmp=generated[1];tmp.previous_hash[0]^=1u;
    CHECK(tb_receipt_verify_chain(&tmp,1,NULL)==TB_ERR_MISMATCH);
    CHECK(tb_receipt_verify_chain(&generated[1],2,NULL)==TB_ERR_MISMATCH);
    tmp=generated[1];tmp.previous_hash[0]^=1u;
    generated[1]=tmp;
    CHECK(tb_receipt_verify_chain(generated,3,NULL)==TB_ERR_MISMATCH);
    generated[1]=parsed[1];
    CHECK(tb_receipt_verify_chain(generated,3,NULL)==TB_OK);
    CHECK(tb_receipt_verify_chain(generated,2,NULL)==TB_OK); /* truncated unanchored chain */
    CHECK(tb_receipt_verify_chain(generated,2,generated[2].receipt_hash)==TB_ERR_MISMATCH);

    CHECK(tb_receipt_encode(&generated[0],canonical,10u,&written)==TB_ERR_LENGTH);
    CHECK(tb_receipt_encode(&generated[0],canonical,sizeof(canonical),&written)==TB_OK);
    CHECK(tb_receipt_parse(canonical,written,&tmp)==TB_OK);
    bad("{}",2,TB_ERR_FORMAT);
    {
        const char *duplicates = "{\"version\":1,\"\\u0076ersion\":1}";
        const char *unknown = "{\"unknown\":1}";
        const char *surrogate = "{\"kind\":\"\\uD800\"}";
        bad(duplicates,strlen(duplicates),TB_ERR_FORMAT);
        bad(unknown,strlen(unknown),TB_ERR_FORMAT);
        bad(surrogate,strlen(surrogate),TB_ERR_FORMAT);
    }
    bad("{\"version\":1,\"version\":1}",25,TB_ERR_FORMAT);
    bad("{\"version\":2}",13,TB_ERR_FORMAT);
    bad("{\"version\":1e0}",15,TB_ERR_FORMAT);
    bad("{\"version\":1.0}",15,TB_ERR_FORMAT);
    bad("{\"version\":-1}",14,TB_ERR_FORMAT);
    bad("{\"kind\":\"\\uD800\"}",17,TB_ERR_FORMAT);
    bad(canonical,written-1u,TB_ERR_FORMAT);
    CHECK(written+1u<sizeof(modified));
    memcpy(modified,canonical,written);
    modified[written]='x';
    bad(modified,written+1u,TB_ERR_FORMAT);
    memcpy(modified,canonical,written);
    {
        char *p=strstr(modified,"\"explicit-delete\"");
        CHECK(p!=NULL);
        p[1]='X';
    }
    bad(modified,written,TB_ERR_FORMAT);
    memcpy(modified,canonical,written);
    {
        char *p=strstr(modified,hashes[0]);
        CHECK(p!=NULL);
        p[0]='0'; /* digest tampering */
    }
    bad(modified,written,TB_ERR_MISMATCH);
    memcpy(modified,canonical,written);
    {
        char *p=strstr(modified,"\"version\":1");
        CHECK(p!=NULL);
        p[10]='2'; /* version must be 1 */
    }
    bad(modified,written,TB_ERR_FORMAT);
    tmp=generated[0];
    tmp.evidence.deleted_size=0; /* forged explicit deletion */
    CHECK(tb_receipt_encode(&tmp,canonical,sizeof(canonical),&written)==TB_ERR_FORMAT);
    tmp=generated[0];
    tmp.receipt_hash[0]^=1u;
    CHECK(tb_receipt_encode(&tmp,canonical,sizeof(canonical),&written)==TB_ERR_MISMATCH);
    CHECK(tb_receipt_create(NULL,NULL,&tmp)==TB_ERR_ARGUMENT);
    CHECK(tb_receipt_parse(NULL,0,&tmp)==TB_ERR_ARGUMENT);
    CHECK(tb_receipt_parse(canonical,0,NULL)==TB_ERR_ARGUMENT);
    puts("PASS: Phase 3 golden receipts, strict parser, canonical JSON and tamper-checked chains");
    return 0;
}
