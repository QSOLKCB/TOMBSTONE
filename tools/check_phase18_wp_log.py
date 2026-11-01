#!/usr/bin/env python3
"""Reject vacuous, missing, warning-only and partial Phase 18 WP reports."""
from pathlib import Path
import re
import sys

def validate(s: str) -> int:
    matches=re.findall(r"Proved goals:\s*(\d+)\s*/\s*(\d+)",s)
    if len(matches)!=1:
        raise ValueError("expected one unambiguous WP proof summary")
    proved,total=map(int,matches[0])
    if total==0 or proved!=total:
        raise ValueError("missing, vacuous or incomplete WP goals")
    if "tb_receipt_verify_chain" not in s:
        raise ValueError("missing real public C99 verifier name in solver evidence")
    if re.search(r"\b(Timeout|Timeouts|unknown goal|Error:|WP error|not proved)\b",s,re.I):
        raise ValueError("solver timeout/error or undischarged obligation")
    return total

def main() -> None:
    if len(sys.argv)!=2:
        raise SystemExit("usage: check_phase18_wp_log.py <log>")
    try:
        total=validate(Path(sys.argv[1]).read_text(encoding="utf-8",errors="replace"))
    except (OSError,ValueError) as err:
        raise SystemExit("FAIL: Phase 18 unbounded proof incomplete: "+str(err)) from err
    print(f"PASS: Phase 18 unbounded production verifier WP: {total}/{total} nonzero goals")
    print("LIMIT: SHA and digest equality provider contracts are explicitly assumed")

if __name__=="__main__":
    main()
