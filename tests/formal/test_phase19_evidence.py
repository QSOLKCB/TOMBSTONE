#!/usr/bin/env python3
"""Prevent Phase 19 imported 11/11+40/40 from promoting the bridge or SHA."""
import copy
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import check_phase19_evidence as gate
original=gate.read()
gate.verify(original)
def reject(label,modify):
    x=copy.deepcopy(original)
    modify(x)
    try:gate.verify(x)
    except (AssertionError,ValueError,KeyError,TypeError):return
    raise AssertionError("unjustified Phase 19 proof promotion: "+label)
reject("vacuous",lambda x:x["targets"][0].update(proved=0,goal_count=0))
reject("partial",lambda x:x["targets"][1].update(proved=39))
reject("wrong SHA",lambda x:x["source"].update(git_blob_sha="0"*40))
reject("wrong proof",lambda x:x["targets"][1].update(overlay_git_blob_sha="0"*40))
reject("wrong checkout",lambda x:x["reported_execution"].update(ci_checkout_sha="0"*40))
reject("wrong run",lambda x:x["reported_execution"].update(workflow_run_id=1))
reject("no RTE",lambda x:x["reported_execution"].update(rte_enabled=False))
reject("bridge inflated",lambda x:x["residual"][0].update(status="PROVED"))
reject("bridge list erased",lambda x:x.update(residual=[]))
reject("unscoped",lambda x:x.update(promotion="END_TO_END_PROVED"))
reject("rejected erased",lambda x:x.update(rejected_attempts=[]))
reject("tag altered",lambda x:x["release"].update(modified=True))
print("PASS: 12 stale, vacuous, partial, overstated, or forged Phase 19 evidence cases rejected")
