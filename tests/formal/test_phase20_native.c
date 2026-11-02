/* SPDX-License-Identifier: Apache-2.0 */
/* Finite native evidence, not a universal JSON or provider theorem. */
#include "tombstone/receipt.h"
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int p20_mutation_active;
#ifndef P20_SOURCE
#define P20_SOURCE "../../src/encoding/receipt.c"
#endif
#include P20_SOURCE

#define CHECK(p, tag) do { if (!(p)) { \
    fprintf(stderr,"FAIL[%s] %s:%d: %s\n",tag,__FILE__,__LINE__,#p); exit(1); \
} } while (0)
/* Link-time interposition is invisible to compiler builtin analysis. */
static volatile unsigned calls, fail_at;
static volatile int truncate_result;
static unsigned validation_cases, format_cases, fault_cases;
static unsigned shared_cases, shared_faults;

static int wrapped_format(char *s,size_t n,const char *format,va_list args)
{
    ++calls;
    if (calls == fail_at) return truncate_result ? (int)n : -1;
    return vsnprintf(s,n,format,args);
}
int __wrap_snprintf(char *s,size_t n,const char *format,...)
{
    va_list args; int result;
    va_start(args,format); result=wrapped_format(s,n,format,args); va_end(args);
    return result;
}
int __wrap___snprintf_chk(char *s,size_t n,int flag,size_t object_size,
                         const char *format,...)
{
    va_list args; int result;
    (void)flag; CHECK(n <= object_size,"FORTIFY_SIZE");
    va_start(args,format); result=wrapped_format(s,n,format,args); va_end(args);
    return result;
}

static void validate(const tb_receipt_v1 *r,int expected)
{
    tb_receipt_v1 saved;
    memcpy(&saved,r,sizeof(saved));
    CHECK(good_receipt(r) == expected,expected ? "VALIDATION_ACCEPT" : "VALIDATION_REJECT");
    CHECK(memcmp(&saved,r,sizeof(saved)) == 0,"VALIDATOR_FRAME");
    ++validation_cases;
}
static void validator_cases(const tb_receipt_v1 receipts[3])
{
    tb_receipt_v1 r;
    unsigned i;
    for (i=0;i<3;++i) {
        validate(&receipts[i],1);
        r=receipts[i]; r.has_previous=2; validate(&r,0);
        r=receipts[i]; r.evidence.kind=(tb_evidence_kind)99; validate(&r,0);
        r=receipts[i]; r.evidence.before_size=(size_t)TB_EVIDENCE_MAX_BYTES+1; validate(&r,0);
        r=receipts[i]; r.evidence.after_size=(size_t)TB_EVIDENCE_MAX_BYTES+1; validate(&r,0);
        r=receipts[i]; r.evidence.deleted_size=(size_t)TB_EVIDENCE_MAX_BYTES+1; validate(&r,0);
        r=receipts[i]; r.evidence.deleted_offset=(size_t)TB_EVIDENCE_MAX_BYTES+1; validate(&r,0);
    }
    r=receipts[0]; r.evidence.deleted_size=0; validate(&r,0);
    r=receipts[0]; r.evidence.deleted_size=r.evidence.before_size+1; validate(&r,0);
    r=receipts[0]; ++r.evidence.after_size; validate(&r,0);
    r=receipts[0]; r.evidence.deleted_offset=r.evidence.after_size+1; validate(&r,0);
    r=receipts[0]; r.evidence.deleted_offset=r.evidence.after_size; validate(&r,1);
    r=receipts[0]; r.evidence.deleted_offset=0; validate(&r,1);
    r=receipts[2]; ++r.evidence.after_size; validate(&r,0);
    r=receipts[2]; r.evidence.kind=TB_EVIDENCE_OBSERVED_TRANSITION; validate(&r,0);
    r=receipts[2]; r.evidence.kind=TB_EVIDENCE_OBSERVED_TRANSITION;
    ++r.evidence.after_size; validate(&r,1);
    r=receipts[2]; r.evidence.deleted_size=1; validate(&r,0);
    r=receipts[2]; r.evidence.deleted_offset=1; validate(&r,0);
    for (i=0;i<32;++i) {
        r=receipts[0]; r.previous_hash[i]=1; validate(&r,0);
        r=receipts[2]; r.evidence.deleted_sha256[i]=1; validate(&r,0);
        r=receipts[2]; r.evidence.after_sha256[i]^=1; validate(&r,0);
        r.evidence.kind=TB_EVIDENCE_OBSERVED_TRANSITION; validate(&r,1);
    }
}

static void format_case(const tb_receipt_v1 *r,int with_hash,const char *expected,
                        size_t capacity,unsigned injected_call,int truncation)
{
    unsigned char storage[TB_RECEIPT_JSON_MAX+32];
    tb_receipt_v1 saved;
    size_t i,written=(size_t)0xa5a5,needed=strlen(expected);
    tb_status status;
    CHECK(capacity <= TB_RECEIPT_JSON_MAX,"TEST_CAPACITY");
    memcpy(&saved,r,sizeof(saved)); memset(storage,0xa5,sizeof(storage));
    calls=0; fail_at=injected_call; truncate_result=truncation;
    status=format_json(r,with_hash,(char *)storage+16,capacity,&written);
    CHECK(memcmp(&saved,r,sizeof(saved)) == 0,"FORMAT_INPUT_FRAME");
    for (i=0;i<16;++i) CHECK(storage[i] == 0xa5,"FORMAT_LEFT_FRAME");
    for (i=16+capacity;i<sizeof(storage);++i) CHECK(storage[i] == 0xa5,"FORMAT_RIGHT_FRAME");
    if (injected_call || capacity <= needed) {
        if (status != TB_ERR_LENGTH) fprintf(stderr,"format case: capacity=%zu needed=%zu inject=%u calls=%u truncation=%d status=%d\n",capacity,needed,injected_call,calls,truncation,status);
        CHECK(status == TB_ERR_LENGTH,"FORMAT_ERROR_STATUS");
        CHECK(written == (size_t)0xa5a5,"ERROR_SIZE");
        if (injected_call) CHECK(calls == injected_call,"ERROR_STOPS_CALLS");
        if (injected_call) ++fault_cases;
    } else {
        CHECK(status == TB_OK,"FORMAT_OK");
        CHECK(written == needed && written < capacity,"FORMAT_SIZE");
        CHECK(storage[16+written] == 0,"FORMAT_NUL");
        CHECK(memcmp(storage+16,expected,needed) == 0,"FORMAT_GOLDEN_BYTES");
    }
    ++format_cases; fail_at=0;
}

/* Valid disjoint regions need not occupy different malloc allocations. Check
 * every byte of this allocation outside the output and size write footprints,
 * including padding and the unused region on the other side of the receipt. */
static void shared_case(const tb_receipt_v1 *r,int with_hash,const char *expected,
                        size_t capacity,unsigned injected_call,int truncation,
                        int output_after,size_t offset)
{
    struct allocation {
        unsigned char before[TB_RECEIPT_JSON_MAX+32];
        tb_receipt_v1 receipt;
        size_t written;
        unsigned char after[TB_RECEIPT_JSON_MAX+32];
    } *block=malloc(sizeof(*block));
    unsigned char saved[sizeof(*block)],*bytes,*output;
    size_t i,output_start,size_start,needed=strlen(expected);
    tb_status status;
    CHECK(block != NULL,"SHARED_ALLOCATION");
    CHECK(capacity <= TB_RECEIPT_JSON_MAX && offset <= 16,"SHARED_CAPACITY");
    memset(block,0xa5,sizeof(*block));
    memcpy(&block->receipt,r,sizeof(*r)); block->written=(size_t)0xa5a5;
    memcpy(saved,block,sizeof(*block)); bytes=(unsigned char *)block;
    output=(output_after ? block->after : block->before)+offset;
    output_start=(size_t)(output-bytes);
    size_start=(size_t)((unsigned char *)&block->written-bytes);
    calls=0; fail_at=injected_call; truncate_result=truncation;
    status=format_json(&block->receipt,with_hash,(char *)output,capacity,&block->written);
    for (i=0;i<sizeof(*block);++i) {
        if (i>=output_start && i-output_start<capacity) continue;
        if (i>=size_start && i-size_start<sizeof(block->written)) continue;
        CHECK(bytes[i] == saved[i],"SHARED_CALLER_FRAME");
    }
    if (injected_call || capacity <= needed) {
        CHECK(status == TB_ERR_LENGTH,"SHARED_ERROR_STATUS");
        CHECK(block->written == (size_t)0xa5a5,"SHARED_ERROR_SIZE");
        if (injected_call) {
            CHECK(calls == injected_call,"SHARED_ERROR_STOPS_CALLS");
            ++shared_faults;
        }
    } else {
        CHECK(status == TB_OK,"SHARED_FORMAT_OK");
        CHECK(block->written == needed && block->written < capacity,"SHARED_FORMAT_SIZE");
        CHECK(output[block->written] == 0,"SHARED_FORMAT_NUL");
        CHECK(memcmp(output,expected,needed) == 0,"SHARED_GOLDEN_BYTES");
    }
    ++shared_cases; fail_at=0; free(block);
}

int main(int argc,char **argv)
{
    static const char *paths[]={"machine/examples/explicit-delete-v1.json",
        "machine/examples/observed-transition-v1.json","machine/examples/unchanged-v1.json"};
    tb_receipt_v1 receipts[3];
    char golden[3][TB_RECEIPT_JSON_MAX],without_hash[TB_RECEIPT_JSON_MAX];
    size_t i,n,capacity;
    int with_hash,truncation;
    CHECK(argc == 4,"ORACLE_PATHS");
    for (i=0;i<3;++i) {
        FILE *file=fopen(paths[i],"rb"); CHECK(file != NULL,"FIXTURE_OPEN");
        n=fread(golden[i],1,sizeof(golden[i]),file);
        CHECK(!ferror(file) && feof(file) && n < sizeof(golden[i]),"FIXTURE_READ");
        CHECK(fclose(file) == 0,"FIXTURE_CLOSE");
        CHECK(tb_receipt_parse(golden[i],n,&receipts[i]) == TB_OK,"FIXTURE_PARSE");
        file=fopen(argv[i+1],"rb"); CHECK(file != NULL,"ORACLE_OPEN");
        n=fread(golden[i],1,sizeof(golden[i]),file);
        CHECK(!ferror(file) && feof(file) && n < sizeof(golden[i]),"ORACLE_READ");
        CHECK(fclose(file) == 0,"ORACLE_CLOSE");
        golden[i][n]='\0';
    }
    /* Test-only mutations are enabled after the unmodified fixture loader,
     * so a parser/setup failure cannot masquerade as a negative control. */
    p20_mutation_active=1;
    validator_cases(receipts);
    for (i=0;i<3;++i) {
        const char *field=strstr(golden[i],",\"receipt_hash\":\"");
        size_t prefix;
        CHECK(field != NULL,"FROZEN_HASH_FIELD");
        prefix=(size_t)(field-golden[i]);
        CHECK(field[17+64] == '"',"FROZEN_HASH_WIDTH");
        memcpy(without_hash,golden[i],prefix);
        strcpy(without_hash+prefix,field+17+64+1);
        for (with_hash=0;with_hash<=1;++with_hash) {
            const char *expected=with_hash ? golden[i] : without_hash;
            unsigned call_count,call;
            for (capacity=1;capacity<=strlen(expected)+2;++capacity)
                format_case(&receipts[i],with_hash,expected,capacity,0,0);
            call_count=calls;
            CHECK(call_count > 0,"FORMAT_CALLS_OBSERVED");
            for (call=1;call<=call_count;++call)
                for (truncation=0;truncation<=1;++truncation)
                    format_case(&receipts[i],with_hash,expected,TB_RECEIPT_JSON_MAX,call,truncation);
            {
                static const size_t offsets[]={1,7,16};
                size_t capacities[]={1,strlen(expected),strlen(expected)+1,TB_RECEIPT_JSON_MAX};
                size_t o,c;
                int after;
                for (after=0;after<=1;++after) for (o=0;o<3;++o) {
                    for (c=0;c<4;++c)
                        shared_case(&receipts[i],with_hash,expected,capacities[c],0,0,after,offsets[o]);
                    for (call=1;call<=call_count;++call)
                        for (truncation=0;truncation<=1;++truncation)
                            shared_case(&receipts[i],with_hash,expected,TB_RECEIPT_JSON_MAX,
                                        call,truncation,after,offsets[o]);
                }
            }
        }
    }
    printf("PASS: %u validator cases; %u formatter cases including %u injected failures; frozen bytes, bounds and frames\n",
           validation_cases,format_cases,fault_cases);
    CHECK(shared_cases == 324 && shared_faults == 180,"SHARED_CASE_INVENTORY");
    printf("PASS: %u same-allocation cases including %u injected failures; disjoint regions, bytes and caller frames\n",
           shared_cases,shared_faults);
    return 0;
}
