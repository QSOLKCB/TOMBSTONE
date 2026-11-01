#!/usr/bin/env python3
"""Build ACSL overlay from the EXACT production receipt.c bytes.

Only inserts ACSL comments. Stripping those precisely restores the frozen
source bytes. No separate/verifier implementation, provider stub or mutation.
The calculate_hash and equal32 contracts are assumptions for THIS one WP
target, not independently discharged theorems about those implementations.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/encoding/receipt.c"
EXPECTED_BLOB = "6fe3e8014e9c38ea42c43b9133f026967a4158e3"

ANNOTATIONS = {
    "static int equal32(const unsigned char *a, const unsigned char *b)": r"""/*@
  requires \valid_read(a+(0 .. 31));
  requires \valid_read(b+(0 .. 31));
  assigns \nothing;
  ensures \result == 0 || \result == 1;
  ensures \result == 1 <==>
    (\forall integer k; 0 <= k < 32 ==> a[k] == b[k]);
*/
""",
    "static tb_status calculate_hash(const tb_receipt_v1 *r, unsigned char out[32])": r"""/*@
  requires \valid_read(r);
  requires \valid(out+(0 .. 31));
  requires \separated(r, out+(0 .. 31));
  assigns out[0 .. 31];
  ensures \result == TB_OK || \result == TB_ERR_FORMAT ||
          \result == TB_ERR_CRYPTO || \result == TB_ERR_MEMORY ||
          \result == TB_ERR_LENGTH || \result == TB_ERR_STATE;
*/
""",
    "tb_status tb_receipt_verify_chain(const tb_receipt_v1 *receipts,size_t count,": r"""/*@
  requires 1 <= count <= SIZE_MAX / sizeof(tb_receipt_v1);
  requires \valid_read(receipts+(0 .. count-1));
  requires trusted_head == \null ||
           \valid_read(trusted_head+(0 .. 31));
  assigns \nothing;
  ensures \result == TB_OK ==> receipts[0].has_previous == 0;
  ensures \result == TB_OK ==>
    (\forall integer j; 1 <= j < count ==> receipts[j].has_previous != 0);
  ensures \result == TB_OK ==>
    (\forall integer j; 1 <= j < count ==>
      (\forall integer k; 0 <= k < 32 ==>
        receipts[j].previous_hash[k] == receipts[j-1].receipt_hash[k]));
  ensures \result == TB_OK && trusted_head != \null ==>
    (\forall integer k; 0 <= k < 32 ==>
      trusted_head[k] == receipts[count-1].receipt_hash[k]);
*/
""",
    "    for(i=0;i<count;++i) {\n        if(i==0u)": r"""    /*@
      loop invariant 0 <= i <= count;
      loop invariant i > 0 ==> receipts[0].has_previous == 0;
      loop invariant
        (\forall integer j; 1 <= j < i ==> receipts[j].has_previous != 0);
      loop invariant
        (\forall integer j; 1 <= j < i ==>
          (\forall integer k; 0 <= k < 32 ==>
            receipts[j].previous_hash[k] == receipts[j-1].receipt_hash[k]));
      loop assigns i, st, computed[0 .. 31];
      loop variant count - i;
    */
""",
}

def git_blob(value: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(value)).encode("ascii") + b"\0" + value).hexdigest()

def render(source: str) -> str:
    rendered = source
    for marker, prefix in ANNOTATIONS.items():
        if source.count(marker) != 1:
            raise ValueError("source location not unique/missing: " + marker[:60])
        rendered = rendered.replace(marker, prefix + marker, 1)
    # Mechanical source identity, not just semantic plausibility.
    stripped = rendered
    for prefix in ANNOTATIONS.values():
        if stripped.count(prefix) != 1:
            raise ValueError("annotation identity mismatch")
        stripped = stripped.replace(prefix, "", 1)
    if stripped != source:
        raise ValueError("overlay does not reduce to exact C99 source")
    return rendered

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    content = SOURCE.read_bytes()
    if git_blob(content) != EXPECTED_BLOB:
        raise SystemExit("FAIL: Phase 18 production C99 source changed")
    data = render(content.decode("utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(data, encoding="utf-8")
    print("PASS: ACSL overlay generated from pinned, unchanged real C99 chain verifier")
    print("LIMIT: assumed calculate_hash/equal32 contracts require separate verification")

if __name__ == "__main__":
    main()
