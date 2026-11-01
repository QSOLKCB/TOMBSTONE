#!/usr/bin/env python3
"""Fail closed on missing targets/RTE, partial proofs, or nonsemantic mutants."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "machine/formal/phase19-bridge-goals-v1.json"
DIAGNOSTICS = ROOT / "machine/formal/phase19-bridge-diagnostics-v1.json"
TARGETS = ("equal32", "calculate_hash", "tb_receipt_verify_chain")
REQUIRED = {
    "equal32": ("ensures", "ensures_2"),
    "calculate_hash": ("ensures_cleanup", "ensures_caller_receipt",
                       "ensures_failure_preserves_output"),
    "tb_receipt_verify_chain": ("ensures", "ensures_2", "ensures_3", "ensures_4",
                                "ensures_cleanup", "ensures_caller_receipts", "ensures_caller_head"),
}
NEGATIVE = {
    "missing-cleanup": r"bytes_calculate_hash_ensures_cleanup\b",
    "caller-corruption": r"bytes_calculate_hash_ensures_caller_receipt\b",
    "double-cleanup": r"bytes_calculate_hash_call_tb_sha256_free.*_requires(?:_\d+)?\b",
}


def unique_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate structured evidence key")
        result[key] = value
    return result


def warnings(text):
    """Retain full diagnostics, normalizing only the generated path and line."""
    blocks = re.findall(r"(?m)^\[[^\]\n]+\] [^\n]*Warning:\s*\n(?:[ \t]+[^\n]*(?:\n|$))+", text)
    if len(blocks) != len(re.findall(r"Warning:", text)):
        raise ValueError("unrecognized warning format")
    return sorted(re.sub(r"/repo/phase19-(?:bridge|mutant)\.c:\d+", "<overlay>:LINE", b).rstrip()
                  for b in blocks)


def parse(text, target):
    if target not in TARGETS:
        raise ValueError("unknown target")
    if len(re.findall(r"(?m)^32\.1 \(Germanium\)\s*$", text)) != 1:
        raise ValueError("missing/duplicate pinned version")
    if re.findall(r"\[rte:annot\] annotating function (\w+)", text) != [target]:
        raise ValueError("wrong, missing or repeated RTE target")
    if re.search(r"\[.*(?:error|abort|warning).*\]|unsupported|Missing RTE", text, re.I):
        raise ValueError("parser/model/runtime warning or error")
    summary = re.findall(r"\[wp\] Proved goals:\s*(\d+)\s*/\s*(\d+)", text)
    if len(summary) != 1:
        raise ValueError("missing/duplicate proof summary")
    proved, total = map(int, summary[0])
    if not 0 < proved <= total or re.findall(r"\[wp\]\s+(\d+) goals? scheduled", text) != [str(total)]:
        raise ValueError("zero, partial inventory or ambiguous scheduling")
    reports = list(re.finditer(r'(?m)^\[\s*\{\s*"goal"\s*:', text))
    if len(reports) != 1:
        raise ValueError("missing/duplicate original WP JSON report")
    goals, _ = json.JSONDecoder(object_pairs_hook=unique_pairs).raw_decode(text[reports[0].start():])
    if not isinstance(goals, list) or not goals:
        raise ValueError("empty structured proof report")
    valid, failed = [], []
    for goal in goals:
        if not isinstance(goal, dict):
            raise ValueError("malformed structured goal")
        if goal.get("function") != target or goal.get("smoke") is not False:
            raise ValueError("unexpected function or smoke goal in proof inventory")
        verdict = goal.get("verdict")
        if verdict not in ("valid", "timeout", "unknown", "failed", "stepout"):
            raise ValueError("unexecuted or unknown goal verdict")
        if goal.get("passed") is not (verdict == "valid"):
            raise ValueError("goal verdict disagrees with pass flag")
        (valid if verdict == "valid" else failed).append(goal["goal"])
    ids = valid + failed
    if len(valid) != proved or len(ids) != total or len(set(ids)) != total:
        raise ValueError("goal-by-goal inventory disagrees with summary")
    if any(not goal.startswith("bytes_" + target + "_") for goal in ids):
        raise ValueError("unexpected function goal")
    return proved, total, valid, failed


def validate(text, target, mutant=None, inventory=None, diagnostics=None):
    proved, total, valid, failed = parse(text, target)
    if diagnostics is not None and warnings(text) != diagnostics[mutant or target]:
        raise ValueError("changed or unreviewed model diagnostics")
    if mutant:
        if target != "calculate_hash" or mutant not in NEGATIVE:
            raise ValueError("unknown negative target")
        if not proved < total or not any(re.fullmatch(NEGATIVE[mutant], goal) for goal in failed):
            raise ValueError("required semantic obligation did not fail")
    else:
        if proved != total or failed or re.search(r"\[wp\] \[(?:Timeout|Unknown|Failed)\]", text):
            raise ValueError("incomplete positive proof")
        for suffix in REQUIRED[target]:
            if "bytes_" + target + "_" + suffix not in valid:
                raise ValueError("required postcondition/frame goal omitted: " + suffix)
        if inventory is not None and sorted(valid) != inventory[target]:
            raise ValueError("exact goal inventory changed")
    return proved, total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=TARGETS)
    parser.add_argument("log", type=Path)
    parser.add_argument("--mutant", choices=NEGATIVE)
    args = parser.parse_args()
    try:
        inventory = json.loads(INVENTORY.read_text(), object_pairs_hook=unique_pairs)
        diagnostics = json.loads(DIAGNOSTICS.read_text(), object_pairs_hook=unique_pairs)
        counts = validate(args.log.read_text(), args.target, args.mutant, inventory, diagnostics)
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit("FAIL: P19-03 WP gate: " + str(error)) from error
    print(f"PASS: {args.mutant or args.target}: {counts[0]}/{counts[1]}, checked goal-by-goal with RTE")


if __name__ == "__main__":
    main()
