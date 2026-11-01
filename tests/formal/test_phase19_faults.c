/* SPDX-License-Identifier: Apache-2.0 */
/* Actual calculate_hash body + real OpenSSL on successful paths. Linker
 * wrappers inject provider/formatter failures only in this test executable.
 * These finite executions are not a heap-lifetime or provider theorem.
 */
#include "tombstone/receipt.h"
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../../src/encoding/receipt.c"

#define CHECK(p) do { if (!(p)) { fprintf(stderr,"FAIL %s:%d: %s\n",__FILE__,__LINE__,#p); exit(1); } } while (0)
enum fault { NONE, FORMAT, NEW, UPDATE_DOMAIN, UPDATE_JSON, FINAL };
static enum fault selected;
static tb_status injected;
static tb_sha256_ctx *live;
static unsigned new_calls, update_calls, final_calls, free_calls;
static char trace[8];
static size_t trace_size;

static void record(char call) {
    CHECK(trace_size + 1 < sizeof(trace));
    trace[trace_size++] = call;
    trace[trace_size] = '\0';
}

int __wrap_snprintf(char *s, size_t n, const char *format, ...)
{
    va_list args;
    int result;
    if (selected == FORMAT) return -1;
    va_start(args, format);
    result = vsnprintf(s, n, format, args);
    va_end(args);
    return result;
}

/* Ubuntu toolchains may lower snprintf to the fortified libc entrypoint. */
int __wrap___snprintf_chk(char *s, size_t n, int flag, size_t object_size,
                         const char *format, ...)
{
    va_list args;
    int result;
    (void)flag;
    CHECK(n <= object_size);
    if (selected == FORMAT) return -1;
    va_start(args, format);
    result = vsnprintf(s, n, format, args);
    va_end(args);
    return result;
}

tb_status __real_tb_sha256_new(tb_sha256_ctx **out);
tb_status __wrap_tb_sha256_new(tb_sha256_ctx **out)
{
    tb_status status;
    ++new_calls; record('N'); CHECK(live == NULL);
    if (selected == NEW) { *out = NULL; return injected; }
    status = __real_tb_sha256_new(out);
    CHECK(status == TB_OK && *out != NULL);
    live = *out;
    return status;
}

tb_status __real_tb_sha256_update(tb_sha256_ctx *ctx, const void *data, size_t length);
tb_status __wrap_tb_sha256_update(tb_sha256_ctx *ctx, const void *data, size_t length)
{
    ++update_calls; record('U'); CHECK(ctx == live && live != NULL);
    if ((selected == UPDATE_DOMAIN && update_calls == 1) ||
        (selected == UPDATE_JSON && update_calls == 2)) return injected;
    return __real_tb_sha256_update(ctx, data, length);
}

tb_status __real_tb_sha256_final(tb_sha256_ctx *ctx, unsigned char out[32]);
tb_status __wrap_tb_sha256_final(tb_sha256_ctx *ctx, unsigned char out[32])
{
    ++final_calls; record('F'); CHECK(ctx == live && live != NULL);
    if (selected == FINAL) return injected;
    return __real_tb_sha256_final(ctx, out);
}

void __real_tb_sha256_free(tb_sha256_ctx *ctx);
void __wrap_tb_sha256_free(tb_sha256_ctx *ctx)
{
    ++free_calls; record('D'); CHECK(ctx == live && live != NULL);
    __real_tb_sha256_free(ctx);
    live = NULL;
}

static void reset(enum fault fault, tb_status status)
{
    CHECK(live == NULL);
    selected = fault; injected = status;
    new_calls = update_calls = final_calls = free_calls = 0;
    trace_size = 0; trace[0] = '\0';
}

static void check_case(const tb_receipt_v1 *r, enum fault fault,
                       tb_status status, const char *expected_trace)
{
    tb_receipt_v1 saved;
    tb_status actual;
    unsigned char out[32], before[32];
    memcpy(&saved, r, sizeof(saved));
    memset(out, 0xa5, sizeof(out)); memcpy(before, out, sizeof(out));
    reset(fault, status);
    actual = calculate_hash(r, out);
    if (actual != status) {
        fprintf(stderr, "fault %d: expected status %d, got %d\n", fault, status, actual);
        exit(1);
    }
    CHECK(strcmp(trace, expected_trace) == 0);
    CHECK(live == NULL);
    CHECK(memcmp(&saved, r, sizeof(saved)) == 0);
    if (status == TB_OK) CHECK(memcmp(out, r->receipt_hash, 32) == 0);
    else CHECK(memcmp(out, before, 32) == 0);
}

int main(void)
{
    char json[TB_RECEIPT_JSON_MAX];
    size_t size;
    FILE *file;
    tb_receipt_v1 r, invalid;
    /* The frozen fixture supplies the expected digest, independently of this
     * test's provider calls. Parsing uses the actual C99 engine as well. */
    file = fopen("machine/examples/unchanged-v1.json", "rb"); CHECK(file != NULL);
    size = fread(json, 1, sizeof(json), file);
    CHECK(!ferror(file) && size < sizeof(json)); CHECK(fclose(file) == 0);
    CHECK(tb_receipt_parse(json, size, &r) == TB_OK);
    check_case(&r, NONE, TB_OK, "NUUFD");
    invalid = r; invalid.has_previous = 2;
    check_case(&invalid, NONE, TB_ERR_FORMAT, "");
    check_case(&r, FORMAT, TB_ERR_LENGTH, "");
    check_case(&r, NEW, TB_ERR_MEMORY, "N");
    check_case(&r, NEW, TB_ERR_CRYPTO, "N");
    check_case(&r, UPDATE_DOMAIN, TB_ERR_CRYPTO, "NUD");
    check_case(&r, UPDATE_JSON, TB_ERR_CRYPTO, "NUUD");
    check_case(&r, UPDATE_DOMAIN, TB_ERR_LENGTH, "NUD");
    check_case(&r, UPDATE_JSON, TB_ERR_LENGTH, "NUUD");
    check_case(&r, UPDATE_DOMAIN, TB_ERR_STATE, "NUD");
    check_case(&r, UPDATE_JSON, TB_ERR_STATE, "NUUD");
    check_case(&r, FINAL, TB_ERR_CRYPTO, "NUUFD");
    check_case(&r, FINAL, TB_ERR_STATE, "NUUFD");
    puts("PASS: 13 actual calculate_hash success/error paths, frozen digest, input/output preservation and exactly-once cleanup");
    puts("LIMIT: finite failure injection; provider heap lifetime and general cleanup remain unproved");
    return 0;
}
