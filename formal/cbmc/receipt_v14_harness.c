/* SPDX-License-Identifier: Apache-2.0 */
/* Phase 14 bounded symbolic checks of production receipt.c parser helpers.
 * Hashing and I/O are unreachable in these targets; this is not an
 * end-to-end proof of canonical JSON or the cryptographic hash chain.
 */
#include "tombstone/receipt.h"
#include <stddef.h>
#include <stdint.h>
#include <string.h>
extern unsigned int nondet_uint(void);
extern unsigned char nondet_uchar(void);
void __CPROVER_assume(int);
void __CPROVER_assert(int, const char *);
#include "../../src/encoding/receipt.c"

void check_number(void)
{
    char bytes[5];
    tb_parser p;
    size_t result = (size_t)0x5151u, n = nondet_uint();
    uint64_t independent = 0;
    size_t j;
    int ok;
    __CPROVER_assume(n > 0u && n <= 4u);
    for (j = 0u; j < 4u; ++j) {
        bytes[j] = (char)nondet_uchar();
        __CPROVER_assume(bytes[j] >= '0' && bytes[j] <= '9');
    }
    bytes[4] = 0;
    p.s = bytes; p.n = n; p.i = 0u;
    ok = number(&p, &result);
    if (bytes[0] == '0' && n > 1u) {
        /* The actual strict JSON parser rejects multi-digit leading zeros
         * before consuming the first byte or writing its output value. */
        __CPROVER_assert(ok == 0, "leading-zero decimal is rejected");
        __CPROVER_assert(p.i == 0u, "leading-zero rejection preserves cursor");
        __CPROVER_assert(result == (size_t)0x5151u,
                         "leading-zero rejection preserves caller output");
    } else {
        /* Every remaining bounded decimal is legal: no overflow at <=4 digits.
         * Quantify all bytes, rather than exclude the invalid leading-zero
         * family through an assumption. */
        __CPROVER_assert(ok == 1, "legal short decimal parses");
        __CPROVER_assert(p.i == n, "legal decimal consumes exactly n digits");
        for (j = 0u; j < n; ++j)
            independent = independent * 10u + (unsigned int)(bytes[j] - '0');
        __CPROVER_assert(result == (size_t)independent,
                         "parsed value matches independent decimal oracle");
    }
    __CPROVER_assert(p.i <= p.n, "numeric parse cursor always bounded");
}

void check_string_bounds(void)
{
    char bytes[5], output[5];
    tb_parser p;
    unsigned int n = nondet_uint();
    size_t j;
    int ok;
    __CPROVER_assume(n <= 4u);
    for (j = 0u; j < 4u; ++j) bytes[j] = (char)nondet_uchar();
    bytes[4] = 0;
    memset(output, 0xa5, sizeof(output));
    p.s = bytes; p.n = (size_t)n; p.i = 0u;
    ok = string(&p, output, 4u);
    __CPROVER_assert(p.i <= p.n, "string parser never advances past input");
    __CPROVER_assert((unsigned char)output[4] == 0xa5,
                     "string parser respects destination capacity");
    if (ok) {
        int has_terminator = 0;
        for (j = 0u; j < 4u; ++j)
            if (output[j] == '\0') has_terminator = 1;
        __CPROVER_assert(has_terminator,
                         "successful string parser terminates within capacity");
    }
}

void check_whitespace_bounds(void)
{
    char bytes[4];
    tb_parser p;
    unsigned int n = nondet_uint();
    size_t j;
    __CPROVER_assume(n <= 4u);
    for (j = 0u; j < 4u; ++j) bytes[j] = (char)nondet_uchar();
    p.s = bytes; p.n = (size_t)n; p.i = 0u;
    ws(&p);
    __CPROVER_assert(p.i <= p.n, "whitespace cursor never exceeds input");
    for (j = 0u; j < p.i; ++j)
        __CPROVER_assert(bytes[j] == ' ' || bytes[j] == '\t' ||
                         bytes[j] == '\r' || bytes[j] == '\n',
                         "whitespace parser consumes whitespace only");
}
