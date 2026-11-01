/* SPDX-License-Identifier: Apache-2.0 */
/* Compile the real C99 provider against real OpenSSL, using test-only
 * --wrap faults at individual external calls. NO production replacements.
 */
#include "tombstone/fingerprint.h"
#include <openssl/evp.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"FAIL %s:%d %s\n",__FILE__,__LINE__,#x); exit(1); } } while(0)
enum fault {NONE, CALLOC, CTX_NEW, INIT, UPDATE, FINAL, FINAL_SIZE};
static enum fault fault;
static unsigned ac,fc,nc,dc,ic,uc,ec;
void *__real_calloc(size_t,size_t);
void *__wrap_calloc(size_t n,size_t s) {++ac; return fault==CALLOC ? NULL : __real_calloc(n,s);}
void __real_free(void *);
void __wrap_free(void *p) {if(p)++fc; __real_free(p);}
EVP_MD_CTX *__real_EVP_MD_CTX_new(void);
EVP_MD_CTX *__wrap_EVP_MD_CTX_new(void) {
    EVP_MD_CTX *p;
    ++nc; if(fault==CTX_NEW)return NULL;
    p=__real_EVP_MD_CTX_new(); CHECK(p!=NULL); return p;
}
void __real_EVP_MD_CTX_free(EVP_MD_CTX *);
void __wrap_EVP_MD_CTX_free(EVP_MD_CTX *p) {if(p)++dc;__real_EVP_MD_CTX_free(p);}
int __real_EVP_DigestInit_ex(EVP_MD_CTX *,const EVP_MD *,ENGINE *);
int __wrap_EVP_DigestInit_ex(EVP_MD_CTX *c,const EVP_MD *m,ENGINE *e) {
    ++ic;return fault==INIT ? 0 : __real_EVP_DigestInit_ex(c,m,e);
}
int __real_EVP_DigestUpdate(EVP_MD_CTX *,const void *,size_t);
int __wrap_EVP_DigestUpdate(EVP_MD_CTX *c,const void *d,size_t n) {
    ++uc;return fault==UPDATE ? 0 : __real_EVP_DigestUpdate(c,d,n);
}
int __real_EVP_DigestFinal_ex(EVP_MD_CTX *,unsigned char *,unsigned int *);
int __wrap_EVP_DigestFinal_ex(EVP_MD_CTX *c,unsigned char *d,unsigned int *n) {
    int rc; ++ec;if(fault==FINAL)return 0;
    rc=__real_EVP_DigestFinal_ex(c,d,n);if(rc==1&&fault==FINAL_SIZE)*n=31u;
    return rc;
}
static void reset(enum fault f){fault=f;ac=fc=nc=dc=ic=uc=ec=0;}
static void cleanup_observed(void){
    CHECK(ac==1&&fc==1&&nc==1);
    CHECK(dc==(fault==CTX_NEW?0u:1u));
}
static void one_shot(enum fault f,tb_status expect){
    const unsigned char abc[]={'a','b','c'};
    unsigned char out[32],before[32];char hex[65];tb_status got;
    memset(out,0xa5,sizeof(out));memcpy(before,out,sizeof(out));
    reset(f);got=tb_sha256_bytes(abc,sizeof(abc),out);CHECK(got==expect);
    if(got==TB_OK) {
        CHECK(tb_sha256_hex(out,hex)==TB_OK);
        CHECK(strcmp(hex,"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")==0);
    } else CHECK(memcmp(out,before,sizeof(out))==0);
    if(f==CALLOC)CHECK(ac==1&&fc==0&&nc==0&&dc==0);
    else cleanup_observed();
    CHECK(ic==(f==CALLOC||f==CTX_NEW?0u:1u));
    CHECK(uc==(f==NONE||f==UPDATE||f==FINAL||f==FINAL_SIZE?1u:0u));
    CHECK(ec==(f==NONE||f==FINAL||f==FINAL_SIZE?1u:0u));
}
static void early(void){
    unsigned char digest[32],copy[32],v=1u;
    memset(digest,0x5a,sizeof(digest));memcpy(copy,digest,sizeof(copy));
    reset(NONE);
    CHECK(tb_sha256_bytes(NULL,1u,digest)==TB_ERR_ARGUMENT);
    CHECK(tb_sha256_bytes(&v,1u,NULL)==TB_ERR_ARGUMENT);
#if SIZE_MAX > (UINT64_MAX / UINT64_C(8))
    CHECK(tb_sha256_bytes(&v,SIZE_MAX,digest)==TB_ERR_LENGTH);
#endif
    CHECK(memcmp(digest,copy,sizeof(copy))==0);
    CHECK(ac==0&&nc==0);
    reset(NONE);CHECK(tb_sha256_bytes(NULL,0u,digest)==TB_OK);
    CHECK(uc==0&&ec==1);cleanup_observed();
}
static void streamed(void){
    unsigned char v=0x42u,out[32],copy[32];tb_sha256_ctx *ctx=NULL;
    reset(UPDATE);CHECK(tb_sha256_new(&ctx)==TB_OK&&ctx!=NULL);
    CHECK(tb_sha256_update(ctx,&v,1u)==TB_ERR_CRYPTO);
    memset(out,0xa5,sizeof(out));memcpy(copy,out,sizeof(copy));
    CHECK(tb_sha256_final(ctx,out)==TB_ERR_STATE);
    CHECK(tb_sha256_update(ctx,&v,1u)==TB_ERR_STATE);
    CHECK(memcmp(out,copy,sizeof(copy))==0);
    tb_sha256_free(ctx);cleanup_observed();
    reset(FINAL);ctx=NULL;CHECK(tb_sha256_new(&ctx)==TB_OK);
    CHECK(tb_sha256_update(ctx,&v,1u)==TB_OK);
    CHECK(tb_sha256_final(ctx,out)==TB_ERR_CRYPTO);
    CHECK(tb_sha256_final(ctx,out)==TB_ERR_STATE);
    CHECK(memcmp(out,copy,sizeof(copy))==0);
    tb_sha256_free(ctx);cleanup_observed();
}
int main(void){
    one_shot(NONE,TB_OK);one_shot(CALLOC,TB_ERR_MEMORY);
    one_shot(CTX_NEW,TB_ERR_MEMORY);one_shot(INIT,TB_ERR_CRYPTO);
    one_shot(UPDATE,TB_ERR_CRYPTO);one_shot(FINAL,TB_ERR_CRYPTO);
    one_shot(FINAL_SIZE,TB_ERR_CRYPTO);early();streamed();
    puts("PASS: actual C99 provider + real EVP success + injected failure matrix");
    puts("PASS: no caller digest writes on error, C99 cleanup, streaming state");
    puts("LIMIT: these executions do NOT prove OpenSSL or SHA-256 implementation");
    return 0;
}
