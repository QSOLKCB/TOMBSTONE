#!/usr/bin/env python3
"""Full structured WP goal gate; unknown inventories fail closed."""
import argparse
import json
from pathlib import Path
import re
from check_phase19_bridge_log import unique_pairs, warnings

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {s:s for s in ("zero32","equal32","good_evidence","good_receipt","hex32","format_json",
                         "calculate_hash","tb_receipt_verify_chain")}
TARGETS.update({"hex-openssl":"tb_sha256_hex","hex-hacl":"tb_sha256_hex",
                "accept-invalid":"good_receipt","bad-size":"format_json","error-size":"format_json"})
NEGATIVE = {"accept-invalid":"receipt_equivalence","bad-size":"ensures_2","error-size":"size_on_error"}
INVENTORY = ROOT / "machine/formal/phase20-goals-v1.json"


def normalize_diagnostics(items):
    """Ignore only line movement in the six known generated Phase 20 units.

    Preserve the filename, warning text and all model premises. Source hashes
    are checked separately; a location normalization cannot renew evidence.
    """
    location = r"(/repo/phase20-(?:receipt|hex-openssl|hex-hacl|accept-invalid|bad-size|error-size)\.c):\d+\b"
    return sorted(re.sub(location, r"\1:LINE", item) for item in items)


def inventory_entry(entry):
    # Historical inventories retain their original line numbers on disk.
    return dict(entry, diagnostics=normalize_diagnostics(entry["diagnostics"]))


def semantic_failures(result, target):
    """The original semantic property, including its executed branch subgoals."""
    suffix = NEGATIVE[target]
    name = "bytes_" + TARGETS[target] + ("_" if suffix.startswith("ensures") else "_ensures_") + suffix
    return [goal for goal in result["unproved"]
            if re.fullmatch(re.escape(name) + r"(?:_part\d+)?", goal)]


def parse(text,target):
    if target not in TARGETS:
        raise ValueError("unknown target")
    function = TARGETS[target]
    if len(re.findall(r"(?m)^32\.1 \(Germanium\)\s*$",text)) != 1:
        raise ValueError("wrong/missing version")
    if re.findall(r"\[rte:annot\] annotating function (\w+)",text) != [function]:
        raise ValueError("wrong/missing RTE target")
    if re.search(r"\[.*(?:error|abort).*\]|unsupported|Missing RTE|User Error:|Frama-C aborted|Prover .*not found",text,re.I):
        raise ValueError("unsupported or failed tool execution")
    summary = re.findall(r"\[wp\] Proved goals:\s*(\d+)\s*/\s*(\d+)",text)
    if len(summary) != 1:
        raise ValueError("missing/duplicate goal summary")
    proved,total = map(int,summary[0])
    scheduled = re.findall(r"\[wp\]\s+(\d+) goals? scheduled",text)
    if len(scheduled) != 1 or not 0 < int(scheduled[0]) <= total or not 0 < proved <= total:
        raise ValueError("zero/inconsistent scheduled inventory")
    scheduled = int(scheduled[0])
    # WP includes automatic CFG facts in its summary but excludes them from
    # the original JSON report. Account for them explicitly; never invent IDs.
    automatic = {}
    for label in ("Terminating","Unreachable"):
        values = re.findall(r"(?m)^  "+label+r":\s*(\d+)\s*$",text)
        if len(values) > 1:
            raise ValueError("duplicate automatic goal count")
        automatic[label] = int(values[0]) if values else 0
    if scheduled + sum(automatic.values()) != total:
        raise ValueError("scheduled and automatic goals disagree with summary")
    matches = list(re.finditer(r'(?m)^\[\s*\{\s*"goal"\s*:',text))
    if len(matches) != 1:
        raise ValueError("missing/duplicate structured report")
    goals,_ = json.JSONDecoder(object_pairs_hook=unique_pairs).raw_decode(text[matches[0].start():])
    if len(goals) != scheduled or len({g["goal"] for g in goals}) != scheduled:
        raise ValueError("missing/duplicate individual goal")
    good=[];bad=[]
    for goal in goals:
        if goal["function"] != function or goal["smoke"] is not False:
            raise ValueError("wrong function or smoke goal")
        if not goal["goal"].startswith("bytes_"+function+"_"):
            raise ValueError("unexpected goal identifier")
        verdict=goal["verdict"]
        if verdict not in ("valid","timeout","unknown","failed","stepout") or goal["passed"] is not (verdict=="valid"):
            raise ValueError("unexecuted/inconsistent verdict")
        provers=goal["provers"]
        if not provers or any(p["prover"] not in ("qed","Alt-Ergo:2.5.4") for p in provers):
            raise ValueError("unexpected or missing executed prover")
        if any(type(p["success"]) is not int or p["success"] not in (0,1) for p in provers):
            raise ValueError("invalid prover verdict")
        if (any(p["success"] for p in provers)) != (verdict=="valid"):
            raise ValueError("goal and prover verdicts disagree")
        (good if verdict=="valid" else bad).append(goal["goal"])
    if len(good) + sum(automatic.values()) != proved:
        raise ValueError("summary disagrees with goals")
    return {"proved":proved,"total":total,"scheduled":scheduled,"automatic":automatic,
            "valid":sorted(good),"unproved":sorted(bad),"diagnostics":normalize_diagnostics(warnings(text))}


def validate(text,target,inventory):
    result=parse(text,target)
    if target in NEGATIVE:
        if not semantic_failures(result, target):
            raise ValueError("designated semantic obligation did not fail")
        if inventory is not None and inventory[TARGETS[target]]["unproved"]:
            raise ValueError("negative control lacks a complete positive baseline")
    elif result["unproved"]:
        raise ValueError("positive proof is incomplete")
    if inventory is None:
        raise ValueError("execution observed; exact inventory/diagnostics NOT_YET_RECORDED")
    if set(inventory) != set(TARGETS):
        raise ValueError("missing or unexpected proof target")
    if result != inventory_entry(inventory[target]):
        raise ValueError("changed goal inventory, verdicts or model diagnostics")
    return result


if __name__ == "__main__":
    ap=argparse.ArgumentParser();ap.add_argument("target",choices=TARGETS);ap.add_argument("log",type=Path)
    args=ap.parse_args()
    try:
        inventory=json.loads(INVENTORY.read_text(),object_pairs_hook=unique_pairs) if INVENTORY.exists() else None
        result=validate(args.log.read_text(),args.target,inventory)
    except (ValueError,KeyError,OSError,TypeError) as error:
        raise SystemExit("FAIL: Phase 20: "+str(error)) from error
    print(f"PASS: {args.target}: {result['proved']}/{result['total']}; exact structured goals, RTE and model premises")
