/* SPDX-License-Identifier: Apache-2.0 */
/* Phase 11: modular ACSL contracts against the actual public C99 body.
 * This proof translation unit includes the real implementation at the end.
 * SHA-256 is an EXTERNAL ASSUMPTION, not a proven implementation here.
 */
#include "tombstone/deletion.h"

/*@
  requires length == 0 || \valid_read(((const char *)data)+(0 .. length-1));
  requires \valid(out+(0 .. TB_SHA256_DIGEST_SIZE-1));
  requires \separated(((const char *)data)+(0 .. length-1),
                      out+(0 .. TB_SHA256_DIGEST_SIZE-1));
  assigns out[0 .. TB_SHA256_DIGEST_SIZE-1];
  ensures \result == TB_OK || \result == TB_ERR_CRYPTO || \result == TB_ERR_MEMORY;
  ensures \result != TB_OK ==>
    (\forall integer i; 0 <= i < TB_SHA256_DIGEST_SIZE ==>
       out[i] == \at(out[i],Pre));
*/
tb_status tb_sha256_bytes(const void *data, size_t length,
                          unsigned char out[TB_SHA256_DIGEST_SIZE]);

/* Phase 11 modular boundary for the REAL private helper in deletion.c.
 * Each contract must be proved separately; no synthetic implementation.
 */
/*@
  requires \valid(temp);
  requires before_size == 0 ||
    \valid_read(((const char *)before)+(0 .. before_size-1));
  requires after_size == 0 ||
    \valid_read(((const char *)after)+(0 .. after_size-1));
  requires \separated(temp, ((const char *)before)+(0 .. before_size-1));
  requires \separated(temp, ((const char *)after)+(0 .. after_size-1));
  assigns temp->before_sha256[0 .. TB_SHA256_DIGEST_SIZE-1],
          temp->after_sha256[0 .. TB_SHA256_DIGEST_SIZE-1];
  ensures \result == TB_OK || \result == TB_ERR_CRYPTO ||
          \result == TB_ERR_MEMORY;
*/
static tb_status fingerprints(const void *before, size_t before_size,
                              const void *after, size_t after_size,
                              tb_evidence_v1 *temp);

/* Stage proof: the actual private C99 function, under the independently
 * discharged fingerprints contract and still-assumed SHA provider contract.
 */
/*@
  requires \valid(tmp);
  requires before_size == 0 ||
    \valid_read(((const char *)before)+(0 .. before_size-1));
  requires after_size == 0 ||
    \valid_read(((const char *)after)+(0 .. after_size-1));
  requires removed_size == 0 ||
    \valid_read(((const char *)removed)+(0 .. removed_size-1));
  requires \separated(tmp, ((const char *)before)+(0 .. before_size-1));
  requires \separated(tmp, ((const char *)after)+(0 .. after_size-1));
  requires \separated(tmp, ((const char *)removed)+(0 .. removed_size-1));
  assigns *tmp;
  ensures \result == TB_OK || \result == TB_ERR_CRYPTO ||
          \result == TB_ERR_MEMORY;
  ensures \result == TB_OK ==>
    (tmp->kind == TB_EVIDENCE_EXPLICIT_DELETE &&
     tmp->before_size == before_size &&
     tmp->after_size == after_size &&
     tmp->deleted_size == removed_size &&
     tmp->deleted_offset == offset);
*/
static tb_status witness_stage(const void *before, size_t before_size,
                               const void *removed, size_t removed_size,
                               size_t offset, const void *after,
                               size_t after_size, tb_evidence_v1 *tmp);

/* Exact byte identity is mandatory for any successful or hash-reached
 * return. This is an INTENDED contract; full-wrapper WP is not yet proved.
 */
/*@
  requires out != \null ==> \valid(out);
  requires before != \null && before_size <= TB_EVIDENCE_MAX_BYTES ==>
    \valid_read(((const unsigned char *)before)+(0 .. before_size-1));
  requires after != \null && after_size <= TB_EVIDENCE_MAX_BYTES ==>
    \valid_read(((const unsigned char *)after)+(0 .. after_size-1));
  requires removed != \null && removed_size <= TB_EVIDENCE_MAX_BYTES ==>
    \valid_read(((const unsigned char *)removed)+(0 .. removed_size-1));
  requires out != \null && before != \null && before_size <= TB_EVIDENCE_MAX_BYTES ==>
    \separated(out, ((const unsigned char *)before)+(0 .. before_size-1));
  requires out != \null && after != \null && after_size <= TB_EVIDENCE_MAX_BYTES ==>
    \separated(out, ((const unsigned char *)after)+(0 .. after_size-1));
  requires out != \null && removed != \null && removed_size <= TB_EVIDENCE_MAX_BYTES ==>
    \separated(out, ((const unsigned char *)removed)+(0 .. removed_size-1));
  assigns *out;
  ensures \result == TB_OK || \result == TB_ERR_ARGUMENT ||
          \result == TB_ERR_LENGTH || \result == TB_ERR_MISMATCH ||
          \result == TB_ERR_CRYPTO || \result == TB_ERR_MEMORY;
  ensures \result == TB_OK ==>
    (removed_size > 0 && removed_size <= before_size &&
     offset <= before_size - removed_size &&
     after_size == before_size - removed_size &&
     (\forall integer i; 0 <= i < removed_size ==>
       ((const unsigned char *)before)[offset+i] ==
       ((const unsigned char *)removed)[i]) &&
     (\forall integer j; 0 <= j < after_size ==>
       ((const unsigned char *)after)[j] ==
       ((const unsigned char *)before)[j < offset ? j : j+removed_size]));
  ensures \result != TB_ERR_ARGUMENT &&
          \result != TB_ERR_LENGTH &&
          \result != TB_ERR_MISMATCH ==>
    (removed_size > 0 && removed_size <= before_size &&
     offset <= before_size - removed_size &&
     after_size == before_size - removed_size &&
     (\forall integer i; 0 <= i < removed_size ==>
       ((const unsigned char *)before)[offset+i] ==
       ((const unsigned char *)removed)[i]) &&
     (\forall integer j; 0 <= j < after_size ==>
       ((const unsigned char *)after)[j] ==
       ((const unsigned char *)before)[j < offset ? j : j+removed_size]));
  ensures out == \null || \result != TB_OK ||
          (out->kind == TB_EVIDENCE_EXPLICIT_DELETE &&
           out->before_size == before_size &&
           out->after_size == after_size &&
           out->deleted_size == removed_size &&
           out->deleted_offset == offset);
  ensures out == \null || \result == TB_OK ||
    (\forall integer i; 0 <= i < sizeof(*out) ==>
       ((unsigned char *)out)[i] == \at(((unsigned char *)out)[i],Pre));
  ensures (out == \null || (before == \null && before_size > 0) ||
           removed == \null || removed_size == 0 ||
           (after == \null && after_size > 0)) ==>
           \result == TB_ERR_ARGUMENT;
  ensures (out != \null && (before != \null || before_size == 0) &&
           removed != \null && removed_size > 0 &&
           (after != \null || after_size == 0) &&
           (before_size > TB_EVIDENCE_MAX_BYTES ||
            after_size > TB_EVIDENCE_MAX_BYTES ||
            removed_size > TB_EVIDENCE_MAX_BYTES ||
            offset > TB_EVIDENCE_MAX_BYTES ||
            removed_size > before_size ||
            (removed_size <= before_size && offset > before_size-removed_size))) ==>
           \result == TB_ERR_LENGTH;
*/
tb_status tb_witness_delete(const void *before, size_t before_size,
                            const void *removed, size_t removed_size,
                            size_t offset,
                            const void *after, size_t after_size,
                            tb_evidence_v1 *out);

/* Verification inputs are not a separate production implementation. */
#include "../../src/core/deletion.c"
