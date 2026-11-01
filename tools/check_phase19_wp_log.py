#!/usr/bin/env python3
"""Check the complete Phase 19 target, RTE pass and pinned goal count.

This checks an execution report, not the truth of external contracts. The
counts belong to the preserved v1 overlays and Frama-C/WP 32.1 Bytes model.
"""
import argparse
from pathlib import Path
import re

EXPECTED = {"equal32": 11, "calculate_hash": 40, "calculate_hash_errors": 41}
FUNCTION = {target: target for target in EXPECTED}
FUNCTION["calculate_hash_errors"] = "calculate_hash"


def validate(text, target):
    if target not in EXPECTED:
        raise ValueError("unknown Phase 19 proof target")
    if not re.search(r"(?m)^32\.1 \(Germanium\)\s*$", text):
        raise ValueError("missing pinned Frama-C version banner")
    targets = re.findall(r"\[rte:annot\] annotating function (\w+)", text)
    if targets != [FUNCTION[target]]:
        raise ValueError("missing, duplicate or wrong RTE target")
    scheduled = re.findall(r"\[wp\]\s+(\d+) goals? scheduled", text)
    summaries = re.findall(r"\[wp\] Proved goals:\s*(\d+)\s*/\s*(\d+)", text)
    count = EXPECTED[target]
    if scheduled != [str(count)] or summaries != [(str(count), str(count))]:
        raise ValueError("missing, duplicate, partial or changed goal inventory")
    if re.search(r"\b(?:timeout|timeouts|unknown|failed|unproved|not proved)\b|"
                 r"Missing RTE|\[.*(?:error|abort).*\]|unsupported", text, re.I):
        raise ValueError("solver failure, unsupported obligation or missing RTE")
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=EXPECTED)
    parser.add_argument("log", type=Path)
    args = parser.parse_args()
    try:
        count = validate(args.log.read_text(encoding="utf-8"), args.target)
    except (OSError, UnicodeError, ValueError) as error:
        raise SystemExit("FAIL: Phase 19 WP evidence: " + str(error)) from error
    print(f"PASS: {args.target}: {count}/{count}, exact target/version and RTE")


if __name__ == "__main__":
    main()
