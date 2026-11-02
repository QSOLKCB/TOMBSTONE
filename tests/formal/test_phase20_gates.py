#!/usr/bin/env python3
"""Adversarial evidence checks against original, retained solver reports."""
import copy
import json
from pathlib import Path
import re
import hashlib
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import check_phase20_evidence as evidence
import check_phase20_wp as gate
import check_phase20_model_evidence as model_gate

record=evidence.load(evidence.RECORD)
inventory=evidence.load(gate.INVENTORY)
incomplete=evidence.validate(record,require_complete=False)
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
    if target in incomplete or (target in gate.NEGATIVE and gate.TARGETS[target] in incomplete):
        rejects(lambda:gate.validate(log,target,inventory))
    else:
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
rejects(lambda:gate.validate(revised(altered),"good_receipt",inventory),"goal and prover verdicts disagree")
for prover in altered[0]["provers"]:
    prover["success"]=0
rejects(lambda:gate.validate(revised(altered),"good_receipt",inventory),"summary disagrees")
altered=copy.deepcopy(goals);altered[0]["goal"]+="_silently_changed"
rejects(lambda:gate.validate(revised(altered),"good_receipt",inventory),"changed goal inventory")
altered=copy.deepcopy(goals);altered[0]["provers"][0]["prover"]="unrecorded-solver"
rejects(lambda:gate.validate(revised(altered),"good_receipt",inventory),"unexpected or missing executed prover")
rejects(lambda:gate.validate(log.replace('"goal":','"goal":"duplicate", "goal":',1),"good_receipt",inventory),"duplicate structured evidence key")
rejects(lambda:gate.validate(log.replace("20 / 20","0 / 0"),"good_receipt",inventory))

for target in gate.NEGATIVE:
    # A parser failure or a positive, complete body cannot stand in for the
    # designated semantic rejection, even if someone edits the inventory too.
    rejects(lambda:gate.validate("32.1 (Germanium)\n[kernel:annot-error] Failure\n",target,inventory))
    replacement=logs[gate.TARGETS[target]]
    if gate.TARGETS[target] not in incomplete:
        forged={target:gate.parse(replacement,target)}
        rejects(lambda:gate.validate(replacement,target,forged),"designated semantic obligation")

for field,value in (("actual_streaming_sha_provider","PROVED"),("canonical_json_theorem","PROVED"),
                    ("libc_implementation","PROVED"),("original_phase18_global_frame","PROVED"),
                    ("review","APPROVED"),("issue_28","CLOSED")):
    altered=copy.deepcopy(record);altered[field]=value
    rejects(lambda:evidence.validate(altered),"unsupported claim promotion")
altered=copy.deepcopy(record);altered["version"]=True
rejects(lambda:evidence.validate(altered),"invalid version")
altered=copy.deepcopy(record);altered["unknown_claim"]="PROVED"
rejects(lambda:evidence.validate(altered),"unknown/missing evidence field")
altered=copy.deepcopy(record);altered["source_blobs"]["src/encoding/receipt.c"]="0"*40
rejects(lambda:evidence.validate(altered),"stale proof dependency")
altered=copy.deepcopy(record);altered["solver_jobs"][0]["sha256"]="0"*64
rejects(lambda:evidence.validate(altered),"retained original log changed")
altered=copy.deepcopy(record);altered["native_jobs"].pop()
rejects(lambda:evidence.validate(altered),"missing or duplicate current-run evidence job")
altered=copy.deepcopy(record);altered["generated_sha256"]["good_receipt"]="0"*64
rejects(lambda:evidence.validate(altered),"generated source identity mismatch")
altered=copy.deepcopy(record);altered["source_blobs"].pop("tools/phase20_model.py")
rejects(lambda:evidence.validate(altered),"missing=['tools/phase20_model.py']")
altered=copy.deepcopy(record);altered["source_blobs"]["tools/unreviewed.py"]="0"*40
rejects(lambda:evidence.validate(altered),"unexpected=['tools/unreviewed.py']")
altered=copy.deepcopy(record);altered["tool"]["correction_spec_sha256"]="0"*64
rejects(lambda:evidence.validate(altered),"tool/model/RTE identity changed")
altered=copy.deepcopy(record);altered["model_job"]["conclusion"]="failure"
rejects(lambda:evidence.validate(altered),"corrected model and lemma job did not pass")
altered=copy.deepcopy(record);altered["compatibility_job"]["conclusion"]="failure"
rejects(lambda:evidence.validate(altered),"original theorem replay did not pass")
altered=copy.deepcopy(record);altered["compatibility_goals"]["chain"]["proved"]=0
rejects(lambda:evidence.validate(altered),"original theorem inventory or diagnostics changed")
altered=copy.deepcopy(record);altered["model_artifact"]["files"]["result.json"]="0"*64
rejects(lambda:evidence.validate(altered),"retained model output changed")

build=model_gate.validate(record["model_artifact"])
model_gate.identity(logs["good_receipt"],build)
for label in ("SPEC","PLUGIN"):
    altered=re.sub(r"PHASE20_MODEL_"+label+r"_SHA256=[0-9a-f]{64}",
                   "PHASE20_MODEL_"+label+"_SHA256="+"0"*64,logs["good_receipt"])
    rejects(lambda:model_gate.identity(altered,build),"corrected model identity")

# Updating a file hash cannot promote a known contradiction, a partial
# positive canary, or an unproved ghost helper to accepted evidence.
with tempfile.TemporaryDirectory() as directory:
    root=Path(directory)
    copied=root/record["model_artifact"]["directory"]
    shutil.copytree(ROOT/record["model_artifact"]["directory"],copied)
    original=json.loads((copied/"result.json").read_text())
    for family,kind,goal,value in (
        ("corrected",None,"contradictory_values","VALID"),
        ("corrected",None,"destination_before","NOT_PROVED"),
        ("string_lemma","positive","ensures","NOT_PROVED"),
        ("string_lemma","negative","ensures","VALID"),
    ):
        data=copy.deepcopy(original)
        values=data["outcomes"][family]
        if kind is not None:
            values=values[kind]["goals"]
        values[goal]=value
        (copied/"result.json").write_text(json.dumps(data))
        altered=copy.deepcopy(record["model_artifact"])
        altered["files"]["result.json"]=hashlib.sha256((copied/"result.json").read_bytes()).hexdigest()
        rejects(lambda:model_gate.validate(altered,root))
if incomplete:
    rejects(lambda:evidence.validate(record),"positive proof is incomplete")
    altered=copy.deepcopy(record);altered["solver_result"]="COMPLETE_UNDER_EXPLICIT_PREMISES"
    rejects(lambda:evidence.validate(altered),"unsupported solver-result promotion")
    altered=copy.deepcopy(record);altered["incomplete_targets"]=[]
    rejects(lambda:evidence.validate(altered),"unsupported solver-result promotion")
print(f"PASS: {checks} adversarial evidence rejections; incomplete or misidentified proofs remain blocked")
