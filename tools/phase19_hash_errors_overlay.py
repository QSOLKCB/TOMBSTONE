#!/usr/bin/env python3
"""New proof attempt; preserve the original 40-goal overlay and evidence.

The streaming update contract now admits TB_ERR_LENGTH, as the real public
provider does. Final's documented no-write-on-error guarantee is an explicit
external assumption used to prove calculate_hash's error-output preservation.
The private-state frame still does not discharge the Phase 18 bridge.
"""
import argparse
from pathlib import Path

import phase19_calculate_hash_overlay as original

UPDATE_START = original.MODEL.index("/*@\n  requires ctx != \\null;")
UPDATE_END = original.MODEL.index("/*@", UPDATE_START + 3)
UPDATE = original.MODEL[UPDATE_START:UPDATE_END]
UPDATED = UPDATE.replace("\\result == TB_ERR_MEMORY || \\result == TB_ERR_STATE;",
                         "\\result == TB_ERR_MEMORY || \\result == TB_ERR_STATE ||\n"
                         "          \\result == TB_ERR_LENGTH;")
FAILURE = r"""  ensures failure_preserves_output: \result != TB_OK ==>
    (\forall integer k; 0 <= k < 32 ==> out[k] == \old(out[k]));
"""
FINAL_END = "*/\ntb_status tb_sha256_final"
MODEL = original.MODEL.replace(UPDATE, UPDATED, 1).replace(
    FINAL_END, FAILURE + FINAL_END, 1)
HASH_CONTRACT = original.HASH_CONTRACT.replace("*/", FAILURE + "*/", 1)


def render():
    base = original.render()
    rendered = base.replace(original.MODEL, MODEL, 1).replace(
        original.HASH_CONTRACT, HASH_CONTRACT, 1)
    if rendered.replace(MODEL, original.MODEL, 1).replace(
            HASH_CONTRACT, original.HASH_CONTRACT, 1) != base:
        raise ValueError("error-path annotations do not restore the original overlay")
    if UPDATED == UPDATE:
        raise ValueError("provider length-error case was not added")
    return rendered


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(), encoding="utf-8")
    print("PASS: exact actual hash body with explicit provider length-error and no-write premises")
    print("LIMIT: actual provider, cleanup and the original Phase 18 frame remain unproved")


if __name__ == "__main__":
    main()
