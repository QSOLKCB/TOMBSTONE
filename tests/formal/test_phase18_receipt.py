#!/usr/bin/env python3
"""Regression: no stale or inflated Phase 18 WP evidence may pass."""
from pathlib import Path
import copy
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import check_phase18_receipt as m

record=m.load()
m.validate(record)
def negative(label,fn):
    value=copy.deepcopy(record)
    fn(value)
    try:m.validate(value)
    except (AssertionError,KeyError,TypeError,ValueError):return
    raise AssertionError("invalid proof evidence accepted: "+label)

negative("zero goals",lambda x:x["checker"].update(proved=0,total=0))
negative("partial goals",lambda x:x["checker"].update(proved=53))
negative("forged compiler count",lambda x:x["checker"]["provers"].update(Qed=39))
negative("missing RTE",lambda x:x["checker"].update(wp_rte=False))
negative("bounded not unbounded",lambda x:x["checker"].update(unbounded=False))
negative("wrong public function",lambda x:x["checker"].update(function="fake_chain"))
negative("fabricated run",lambda x:x.update(github_run_id=1))
negative("wrong commit",lambda x:x.update(checked_commit_sha="0"*40))
negative("changed C99",lambda x:x["source"].update(git_blob_sha="0"*40))
negative("changed overlay",lambda x:x["overlay_generator"].update(git_blob_sha="0"*40))
negative("unproven SHA removed",lambda x:x["exclusions"].remove("No proof of SHA-256, OpenSSL, HACL* or true digest value"))
negative("provider assumptions dropped",lambda x:x["assumptions"].pop())
negative("fake release",lambda x:x["release"].update(changed=True))
print("PASS: 13 incomplete, stale or overclaimed Phase 18 proof receipts fail closed")
