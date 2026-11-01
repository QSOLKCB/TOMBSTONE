/* SPDX-License-Identifier: Apache-2.0 */
/* Phase 14: execute the ACTUAL C99 parser/encoder/chain with real SHA256.
 * All inputs are public toy fixtures; no plaintext or user paths logged.
 */
#include "tombstone/receipt.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(c) do { if (!(c)) { \
  fprintf(stderr,"FAIL %s:%d: %s\n",__FILE__,__LINE__,#c); exit(1); \
} } while (0)

static size_t read_fixture(const char *name, char *dst, size_t capacity)
{
    char path[128];
    FILE *fp;
    size_t size;
    CHECK(snprintf(path,sizeof(path),"machine/examples/%s",name)>0);
    fp = fopen(path,"rb");
    CHECK(fp!=NULL);
    size = fread(dst,1,capacity,fp);
    CHECK(!ferror(fp) && size<capacity && feof(fp));
    CHECK(fclose(fp)==0);
    return size;
}

static void reject(const char *json, size_t length, tb_status expected)
{
    tb_receipt_v1 actual, saved;
    memset(&actual,0xa5,sizeof(actual));
    saved = actual;
    CHECK(tb_receipt_parse(json,length,&actual)==expected);
    CHECK(memcmp(&actual,&saved,sizeof(actual))==0);
}

static void append_field(const char *src,size_t len,const char *field,
                         char *dest,size_t capacity)
{
    size_t extra=strlen(field);
    CHECK(len!=0u && src[len-1u]=='}' && len+extra+1u<capacity);
    memcpy(dest,src,len-1u);
    memcpy(dest+len-1u,field,extra);
    dest[len-1u+extra]='}';
}

static void replace_once(const char *src,size_t len,const char *old,
                         const char *replacement,char *dest,size_t capacity,
                         size_t *outlen)
{
    const char *where=strstr(src,old);
    size_t prefix,olen=strlen(old),rlen=strlen(replacement);
    CHECK(where!=NULL && len+1u<=capacity);
    prefix=(size_t)(where-src);
    CHECK(len-olen+rlen<capacity);
    memcpy(dest,src,prefix);
    memcpy(dest+prefix,replacement,rlen);
    memcpy(dest+prefix+rlen,src+prefix+olen,len-prefix-olen);
    *outlen=len-olen+rlen;
    dest[*outlen]='\0';
}

static void check_encoder_errors(tb_receipt_v1 *receipt)
{
    char buffer[TB_RECEIPT_JSON_MAX];
    size_t written=(size_t)0x1234u, i;
    tb_receipt_v1 bad=*receipt;
    memset(buffer,0xa5,sizeof(buffer));
    CHECK(tb_receipt_encode(receipt,buffer,1u,&written)==TB_ERR_LENGTH);
    CHECK(written==(size_t)0x1234u);
    for(i=0u;i<sizeof(buffer);++i) CHECK((unsigned char)buffer[i]==0xa5);
    bad.receipt_hash[0]^=1u;
    CHECK(tb_receipt_encode(&bad,buffer,sizeof(buffer),&written)==TB_ERR_MISMATCH);
    CHECK(written==(size_t)0x1234u);
    for(i=0u;i<sizeof(buffer);++i) CHECK((unsigned char)buffer[i]==0xa5);
    bad=*receipt;
    bad.evidence.deleted_size=0u;
    CHECK(tb_receipt_encode(&bad,buffer,sizeof(buffer),&written)==TB_ERR_FORMAT);
    CHECK(written==(size_t)0x1234u);
}

int main(void)
{
    static const char *names[3]={
        "explicit-delete-v1.json",
        "observed-transition-v1.json",
        "unchanged-v1.json"
    };
    char file[2048], canonical[TB_RECEIPT_JSON_MAX], mutated[4096], scratch[4096];
    tb_receipt_v1 receipts[3], reordered[3], tmp;
    size_t len, written=0u, newlen, i;

    for(i=0u;i<3u;++i) {
        len=read_fixture(names[i],file,sizeof(file));
        CHECK(tb_receipt_parse(file,len,&receipts[i])==TB_OK);
        CHECK(tb_receipt_encode(&receipts[i],canonical,sizeof(canonical),&written)==TB_OK);
        CHECK(written>0u && written<sizeof(canonical));
        CHECK(canonical[written-1u]=='}');
        CHECK(tb_receipt_parse(canonical,written,&tmp)==TB_OK);
        CHECK(memcmp(tmp.receipt_hash,receipts[i].receipt_hash,32u)==0);
    }
    CHECK(tb_receipt_verify_chain(receipts,3u,receipts[2].receipt_hash)==TB_OK);
    CHECK(tb_receipt_verify_chain(receipts,3u,NULL)==TB_OK);
    CHECK(tb_receipt_verify_chain(receipts,2u,receipts[2].receipt_hash)==TB_ERR_MISMATCH);
    CHECK(tb_receipt_verify_chain(receipts,0u,NULL)==TB_ERR_ARGUMENT);
    reordered[0]=receipts[1]; reordered[1]=receipts[0]; reordered[2]=receipts[2];
    CHECK(tb_receipt_verify_chain(reordered,3u,NULL)==TB_ERR_MISMATCH);
    reordered[0]=receipts[0]; reordered[1]=receipts[1]; reordered[2]=receipts[2];
    reordered[1].previous_hash[0]^=1u;
    CHECK(tb_receipt_verify_chain(reordered,3u,NULL)==TB_ERR_MISMATCH);
    reordered[1]=receipts[1]; reordered[2].receipt_hash[0]^=1u;
    CHECK(tb_receipt_verify_chain(reordered,3u,NULL)==TB_ERR_MISMATCH);
    reordered[2]=receipts[2]; reordered[0].has_previous=1;
    CHECK(tb_receipt_verify_chain(reordered,3u,NULL)==TB_ERR_MISMATCH);
    check_encoder_errors(&receipts[0]);

    CHECK(tb_receipt_encode(&receipts[0],canonical,sizeof(canonical),&written)==TB_OK);
    canonical[written]='\0';
    append_field(canonical,written,",\"version\":1",mutated,sizeof(mutated));
    reject(mutated,written+strlen(",\"version\":1"),TB_ERR_FORMAT);
    append_field(canonical,written,",\"\\u0076ersion\":1",mutated,sizeof(mutated));
    reject(mutated,written+strlen(",\"\\u0076ersion\":1"),TB_ERR_FORMAT);
    append_field(canonical,written,",\"unknown\":0",mutated,sizeof(mutated));
    reject(mutated,written+strlen(",\"unknown\":0"),TB_ERR_FORMAT);
    replace_once(canonical,written,"\"size\":9","\"size\":9007199254740992",
                 mutated,sizeof(mutated),&newlen);
    reject(mutated,newlen,TB_ERR_FORMAT);
    replace_once(canonical,written,"\"size\":9","\"size\":00",
                 mutated,sizeof(mutated),&newlen);
    reject(mutated,newlen,TB_ERR_FORMAT);
    replace_once(canonical,written,"\"version\":1","\"version\":1.0",
                 mutated,sizeof(mutated),&newlen);
    reject(mutated,newlen,TB_ERR_FORMAT);
    replace_once(canonical,written,"\"version\":1","\"version\":1e0",
                 mutated,sizeof(mutated),&newlen);
    reject(mutated,newlen,TB_ERR_FORMAT);
    replace_once(canonical,written,"\"size\":9","\"size\":-1",
                 mutated,sizeof(mutated),&newlen);
    reject(mutated,newlen,TB_ERR_FORMAT);
    replace_once(canonical,written,"\"format\":\"tombstone.receipt\"",
                 "\"format\":\"\\uD800\"",mutated,sizeof(mutated),&newlen);
    reject(mutated,newlen,TB_ERR_FORMAT);
    replace_once(canonical,written,"\"after\":{",
                 "\"after\":{\"size\":0,",mutated,sizeof(mutated),&newlen);
    reject(mutated,newlen,TB_ERR_FORMAT);
    memcpy(scratch,canonical,written);
    scratch[written]='x';
    reject(scratch,written+1u,TB_ERR_FORMAT);
    scratch[written/2u]='\0';
    reject(scratch,written,TB_ERR_FORMAT);
    reject(canonical,written-1u,TB_ERR_FORMAT);
    CHECK(tb_receipt_parse(canonical,16385u,&tmp)==TB_ERR_LENGTH);

    puts("PASS: actual C99 v1 parser/encoder/chain tamper, duplicate, bounds and no-write controls");
    puts("LIMIT: runtime cases and bounded proofs do not prove arbitrary receipt JSON or external SHA provider");
    return 0;
}
