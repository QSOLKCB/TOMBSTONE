/* SPDX-License-Identifier: Apache-2.0 */
/* Phase 17: CBMC checks ONLY the pre-hash rejection paths of the ACTUAL
 * authoritative C99 tb_receipt_verify_chain, included verbatim below.
 * No mock SHA correctness, receipt parser, or historical-event theorem.
 */
#include "tombstone/receipt.h"
#include <stddef.h>
#include <stdint.h>
extern unsigned int nondet_uint(void);
extern int nondet_int(void);
void __CPROVER_assume(int);
void __CPROVER_assert(int, const char *);
#include "../../src/encoding/receipt.c"

void check_null_and_empty(void)
{
    tb_receipt_v1 record;
    unsigned int n = nondet_uint();
    __CPROVER_assume(n <= 3u);
    tb_status rc = tb_receipt_verify_chain(NULL, (size_t)n, NULL);
    __CPROVER_assert(rc == TB_ERR_ARGUMENT, "null chain always rejects before SHA");
    rc = tb_receipt_verify_chain(&record, 0u, NULL);
    __CPROVER_assert(rc == TB_ERR_ARGUMENT, "zero count rejects before SHA");
}

void check_genesis_nonzero(void)
{
    tb_receipt_v1 record;
    record.has_previous = nondet_int();
    __CPROVER_assume(record.has_previous != 0);
    record.receipt_hash[0] = 0xa5;
    tb_status rc = tb_receipt_verify_chain(&record, 1u, NULL);
    __CPROVER_assert(rc == TB_ERR_MISMATCH,
        "nonzero genesis predecessor flag rejects before any digest");
    __CPROVER_assert(record.has_previous != 0,
        "reject does not change genesis predecessor flag");
    __CPROVER_assert(record.receipt_hash[0] == 0xa5,
        "reject does not change caller's receipt digest");
}

void check_oversized_count(void)
{
    tb_receipt_v1 record;
    size_t size = (size_t)-1;
    tb_status rc = tb_receipt_verify_chain(&record, size, NULL);
    __CPROVER_assert(rc == TB_ERR_ARGUMENT,
        "oversized count rejects before dereferencing the small array");
}
