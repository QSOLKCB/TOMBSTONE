#!/usr/bin/env python3
"""Versioned caller-frame composition, NOT the original Phase 18 global frame.

The three actual bodies share one contract environment. Only declarations and
ACSL annotations are added; strip() must restore every production source byte.
The private effect byte and ownership/protocol tokens abstract external calls.
They do not implement SHA, malloc/free, or prove the provider refinement.
"""
import argparse
from pathlib import Path

import phase18_wp_overlay as p18
import phase19_calculate_hash_overlay as p19
import phase19_equal32_overlay as eq
from phase19_hash_errors_overlay import FAILURE

PRIVATE = "p19_effect, p19_owner, p19_phase"
ADDRESSES = "&p19_effect, &p19_owner, &p19_phase"
MODEL = r"""/* P19-03 external premises. Abstract state, not actual heap storage.
 * phase: 0 idle, 1 allocated, 2 first update succeeded,
 * 3 second update succeeded, 4 failed or finalized (cleanup required).
 * owner is a linear call-protocol token, not a proved malloc allocation.
 * effect may change even after free; no restoration of backend state assumed.
 */
static unsigned char p19_effect __attribute__((unused));
static tb_sha256_ctx *p19_owner __attribute__((unused));
static int p19_phase __attribute__((unused));
/*@
  requires \valid(out_ctx);
  requires \separated(out_ctx, &p19_effect, &p19_owner, &p19_phase);
  requires p19_owner == \null && p19_phase == 0;
  assigns *out_ctx, p19_effect, p19_owner, p19_phase;
  ensures \result == TB_OK || \result == TB_ERR_MEMORY ||
          \result == TB_ERR_CRYPTO || \result == TB_ERR_STATE;
  ensures \result == TB_OK ==>
    *out_ctx != \null && p19_owner == *out_ctx && p19_phase == 1;
  ensures \result != TB_OK ==>
    *out_ctx == \null && p19_owner == \null && p19_phase == 0;
*/
tb_status tb_sha256_new(tb_sha256_ctx **out_ctx);
/*@
  requires ctx != \null && ctx == p19_owner;
  requires p19_phase == 1 || p19_phase == 2;
  requires length == 0 || \valid_read(((const unsigned char *)data)+(0 .. length-1));
  assigns p19_effect, p19_phase;
  ensures \result == TB_OK || \result == TB_ERR_CRYPTO ||
          \result == TB_ERR_MEMORY || \result == TB_ERR_STATE ||
          \result == TB_ERR_LENGTH;
  ensures \result == TB_OK ==> p19_phase == \old(p19_phase) + 1;
  ensures \result != TB_OK ==> p19_phase == 4;
*/
tb_status tb_sha256_update(tb_sha256_ctx *ctx,const void *data,size_t length);
/*@
  requires ctx != \null && ctx == p19_owner;
  requires p19_phase == 3;
  requires \valid(out+(0 .. 31));
  requires \separated(out+(0 .. 31), &p19_effect, &p19_owner, &p19_phase);
  assigns out[0 .. 31], p19_effect, p19_phase;
  ensures \result == TB_OK || \result == TB_ERR_CRYPTO ||
          \result == TB_ERR_MEMORY || \result == TB_ERR_STATE;
  ensures p19_phase == 4;
  ensures \result != TB_OK ==>
    (\forall integer k; 0 <= k < 32 ==> out[k] == \old(out[k]));
*/
tb_status tb_sha256_final(tb_sha256_ctx *ctx,unsigned char out[32]);
/*@
  requires ctx != \null && ctx == p19_owner;
  requires 1 <= p19_phase <= 4;
  assigns p19_effect, p19_owner, p19_phase;
  ensures p19_owner == \null && p19_phase == 0;
*/
void tb_sha256_free(tb_sha256_ctx *ctx);
"""

HASH = p18.ANNOTATIONS[p19.HASH_MARKER].replace(
    "  assigns out[0 .. 31];",
    "  requires p19_owner == \\null && p19_phase == 0;\n"
    f"  requires \\separated(r, {ADDRESSES});\n"
    f"  requires \\separated(out+(0 .. 31), {ADDRESSES});\n"
    f"  assigns out[0 .. 31], {PRIVATE};")
HASH = HASH.replace("*/", FAILURE + r"""  ensures cleanup: p19_owner == \null && p19_phase == 0;
  ensures caller_receipt: \forall integer k; 0 <= k < sizeof(*r) ==>
    ((const unsigned char *)r)[k] == \old(((const unsigned char *)r)[k]);
*/""", 1)

CHAIN_MARKER = "tb_status tb_receipt_verify_chain(const tb_receipt_v1 *receipts,size_t count,"
LOOP_MARKER = "    for(i=0;i<count;++i) {\n        if(i==0u)"
CHAIN = p18.ANNOTATIONS[CHAIN_MARKER].replace(
    "  assigns \\nothing;",
    "  requires p19_owner == \\null && p19_phase == 0;\n"
    f"  requires \\separated(receipts+(0 .. count-1), {ADDRESSES});\n"
    "  requires trusted_head == \\null ||\n"
    f"    \\separated(trusted_head+(0 .. 31), {ADDRESSES});\n"
    f"  assigns {PRIVATE};")
CHAIN = CHAIN.replace("*/", r"""  ensures cleanup: p19_owner == \null && p19_phase == 0;
  ensures caller_receipts: \forall integer k;
    0 <= k < count * sizeof(*receipts) ==>
      ((const unsigned char *)receipts)[k] ==
        \old(((const unsigned char *)receipts)[k]);
  ensures caller_head: trusted_head != \null ==>
    (\forall integer k; 0 <= k < 32 ==>
      trusted_head[k] == \old(trusted_head[k]));
*/""", 1)
LOOP = p18.ANNOTATIONS[LOOP_MARKER].replace(
    "      loop assigns i, st, computed[0 .. 31];",
    "      loop invariant p19_owner == \\null && p19_phase == 0;\n"
    f"      loop assigns i, st, computed[0 .. 31], {PRIVATE};")

ANNOTATIONS = dict(p18.ANNOTATIONS)
ANNOTATIONS.update({p19.HASH_MARKER: HASH, CHAIN_MARKER: CHAIN,
                    LOOP_MARKER: LOOP,
                    "static int good_receipt(const tb_receipt_v1 *r)": p19.GOOD,
                    "static tb_status format_json(const tb_receipt_v1 *r, int with_hash,": p19.FORMAT})


def strip(rendered):
    for fragment in [MODEL, eq.EXT, *ANNOTATIONS.values()]:
        if rendered.count(fragment) != 1:
            raise ValueError("missing/duplicate proof fragment")
        rendered = rendered.replace(fragment, "", 1)
    return rendered


def render():
    data = p18.SOURCE.read_bytes()
    if p18.git_blob(data) != p18.EXPECTED_BLOB:
        raise ValueError("production source drift")
    source = data.decode("utf-8")
    rendered = source
    for marker, contract in ANNOTATIONS.items():
        if source.count(marker) != 1:
            raise ValueError("nonunique actual source marker")
        rendered = rendered.replace(marker, contract + marker, 1)
    if rendered.count(eq.BEFORE) != 1:
        raise ValueError("include marker drift")
    rendered = rendered.replace(eq.BEFORE, eq.BEFORE + MODEL + eq.EXT, 1)
    if strip(rendered) != source:
        raise ValueError("overlay must reduce to byte-identical production C")
    return rendered


MUTANTS = {
    "missing-cleanup": ("    tb_sha256_free(ctx);", "    (void)ctx;"),
    "caller-corruption": ("    tb_sha256_free(ctx);",
                          "    ((tb_receipt_v1 *)r)->has_previous ^= 1;\n    tb_sha256_free(ctx);"),
    "double-cleanup": ("    tb_sha256_free(ctx);",
                       "    tb_sha256_free(ctx);\n    tb_sha256_free(ctx);"),
}


def mutant(name):
    source = render()
    old, new = MUTANTS[name]
    if source.count(old) != 1:
        raise ValueError("nonunique mutation site")
    return source.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mutant", choices=MUTANTS)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(mutant(args.mutant) if args.mutant else render(), encoding="utf-8")
    print("GENERATED:", args.mutant or "exact actual equal32/hash/chain with shared caller-frame contracts")
    print("LIMIT: provider frame, allocation, deallocation, memcmp and formatter remain external premises")


if __name__ == "__main__":
    main()
