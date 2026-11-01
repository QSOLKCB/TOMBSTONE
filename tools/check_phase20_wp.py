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


def parse(text,target):
    if target not in TARGETS:
        raise ValueError("unknown target")
    function = TARGETS[target]
    if len(re.findall(r"(?m)^32\.1 \(Germanium\)\s*$",text)) != 1:
        raise ValueError("wrong/missing version")
    if re.findall(r"\[rte:annot\] annotating function (\w+)",text) != [function]:
        raise ValueError("wrong/missing RTE target")
    if re.search(r"\[.*(?:error|abort).*\]|unsupported|Missing RTE",text,re.I):
        raise ValueError("unsupported or failed tool execution")
    summary = re.findall(r"\[wp\] Proved goals:\s*(\d+)\s*/\s*(\d+)",text)
    if len(summary) != 1:
        raise ValueError("missing/duplicate goal summary")
    proved,total = map(int,summary[0])
    if not 0 < proved <= total or re.findall(r"\[wp\]\s+(\d+) goals? scheduled",text) != [str(total)]:
        raise ValueError("zero/inconsistent scheduled inventory")
    matches = list(re.finditer(r'(?m)^\[\s*\{\s*"goal"\s*:',text))
    if len(matches) != 1:
        raise ValueError("missing/duplicate structured report")
    goals,_ = json.JSONDecoder(object_pairs_hook=unique_pairs).raw_decode(text[matches[0].start():])
    if len(goals) != total or len({g["goal"] for g in goals}) != total:
        raise ValueError("missing/duplicate individual goal")
    good=[];bad=[]
    for goal in goals:
        if goal["function"] != function or goal["smoke"] is not False:
            raise ValueError("wrong function or smoke goal")
        verdict=goal["verdict"]
        if verdict not in ("valid","timeout","unknown","failed","stepout") or goal["passed"] is not (verdict=="valid"):
            raise ValueError("unexecuted/inconsistent verdict")
        (good if verdict=="valid" else bad).append(goal["goal"])
    if len(good) != proved:
        raise ValueError("summary disagrees with goals")
    return {"proved":proved,"total":total,"valid":sorted(good),"unproved":sorted(bad),"diagnostics":warnings(text)}


def validate(text,target,inventory):
    result=parse(text,target)
    if target in NEGATIVE:
        suffix=NEGATIVE[target]
        needle="bytes_"+TARGETS[target]+("_" if suffix.startswith("ensures") else "_ensures_")+suffix
        if not result["unproved"] or needle not in result["unproved"]:
            raise ValueError("designated semantic obligation did not fail")
    elif result["unproved"]:
        raise ValueError("positive proof is incomplete")
    if inventory is None:
        raise ValueError("execution observed; exact inventory/diagnostics NOT_YET_RECORDED")
    if result != inventory[target]:
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
