#!/usr/bin/env python3
"""Adversarial evidence checks against original, retained solver reports."""
import copy
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import check_phase20_evidence as evidence
import check_phase20_wp as gate

record=evidence.load(evidence.RECORD)
inventory=evidence.load(gate.INVENTORY)
evidence.validate(record)
logs={}
for row in record["solver_jobs"]:
    logs.update(evidence.solver_logs((ROOT/row["path"]).read_text()))
checks=0
def rejects(action,reason=None):
    global checks
    try:
        action()
    except (ValueError,KeyError,TypeError) as error:
        if reason is not None and reason not in str(error):
            raise AssertionError(f"wrong rejection: {error}") from error
    else:
        raise AssertionError("invalid proof evidence accepted")
    checks+=1

for target,log in logs.items():
    gate.validate(log,target,inventory)
    rejects(lambda:gate.validate(log.replace("32.1 (Germanium)","32.0 (Germanium)"),target,inventory))
    rejects(lambda:gate.validate(re.sub(r"\[rte:annot\] annotating function \w+","",log),target,inventory))
    rejects(lambda:gate.validate(log+"\n"+log,target,inventory))
    rejects(lambda:gate.validate(log+"\n[wp] unexpected Warning:\n  new assumption\n",target,inventory))
    rejects(lambda:gate.validate(log+"\n[wp] User Error: Prover unavailable\n",target,inventory))
    rejects(lambda:gate.validate(log,target,None))

log=logs["good_receipt"]
start=re.search(r'(?m)^\[\s*\{\s*"goal"\s*:',log).start()
goals,end=json.JSONDecoder().raw_decode(log[start:])
def revised(items,prefix=log[:start]):
    return prefix+json.dumps(items)+log[start+end:]

rejects(lambda:gate.validate(revised(goals[:-1]),"good_receipt",inventory),"missing/duplicate individual goal")
rejects(lambda:gate.validate(revised(goals+[goals[0]]),"good_receipt",inventory),"missing/duplicate individual goal")
altered=copy.deepcopy(goals);altered[0]["verdict"]="timeout";altered[0]["passed"]=False
rejects(lambda:gate.validate(revised(altered),"good_receipt",inventory),"summary disagrees")
altered=copy.deepcopy(goals);altered[0]["goal"]+="_silently_changed"
rejects(lambda:gate.validate(revised(altered),"good_receipt",inventory),"changed goal inventory")
rejects(lambda:gate.validate(log.replace('"goal":','"goal":"duplicate", "goal":',1),"good_receipt",inventory),"duplicate structured evidence key")
rejects(lambda:gate.validate(log.replace("20 / 20","0 / 0"),"good_receipt",inventory))

for target in gate.NEGATIVE:
    # A parser failure or a positive, complete body cannot stand in for the
    # designated semantic rejection, even if someone edits the inventory too.
    rejects(lambda:gate.validate("32.1 (Germanium)\n[kernel:annot-error] Failure\n",target,inventory))
    replacement=logs[gate.TARGETS[target]]
    forged={target:gate.parse(replacement,target)}
    rejects(lambda:gate.validate(replacement,target,forged),"designated semantic obligation")

for field,value in (("actual_streaming_sha_provider","PROVED"),("canonical_json_theorem","PROVED"),
                    ("libc_implementation","PROVED"),("original_phase18_global_frame","PROVED"),
                    ("review","APPROVED"),("issue_28","CLOSED")):
    altered=copy.deepcopy(record);altered[field]=value
    rejects(lambda:evidence.validate(altered),"unsupported claim promotion")
altered=copy.deepcopy(record);altered["source_blobs"]["src/encoding/receipt.c"]="0"*40
rejects(lambda:evidence.validate(altered),"stale proof dependency")
altered=copy.deepcopy(record);altered["solver_jobs"][0]["sha256"]="0"*64
rejects(lambda:evidence.validate(altered),"retained original log changed")
altered=copy.deepcopy(record);altered["native_jobs"].pop()
rejects(lambda:evidence.validate(altered),"missing native compiler/provider tuple")
altered=copy.deepcopy(record);altered["generated_sha256"]["good_receipt"]="0"*64
rejects(lambda:evidence.validate(altered),"generated source identity mismatch")
print(f"PASS: {checks} adversarial proof/evidence rejections; exact positive reports and semantic controls accepted")
