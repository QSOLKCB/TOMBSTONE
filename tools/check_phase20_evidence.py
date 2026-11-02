#!/usr/bin/env python3
"""Bind the current proof inputs to preserved, original executed WP reports."""
import argparse
import hashlib
import json
from pathlib import Path
import re

import check_phase19_bridge_evidence as previous
import check_phase20_wp as gate
import phase20_receipt_overlay as overlay

ROOT=Path(__file__).resolve().parents[1]
RECORD=ROOT/"machine/formal/phase20-evidence-v1.json"
EXECUTION=('e8be500075ee00039a8edf88c013ad28ab9cb9a7', '8f159b36db6755744ebbc903d7fb7fd640b49baa', 41364071336, 'failure', 'PARTIAL_PROOF_AND_UNRECORDED_INVENTORY')
INPUTS=previous.INPUTS | {
    "tools/check_phase19_bridge_evidence.py","tools/check_phase19_bridge_log.py",
    "machine/formal/phase19-bridge-evidence-v1.json",
    "machine/formal/phase19-bridge-goals-v1.json","machine/formal/phase19-bridge-diagnostics-v1.json",
    "tools/phase20_receipt_overlay.py","tools/check_phase20_wp.py",
    "tools/check_phase20_evidence.py","tests/formal/test_phase20_overlay.py",
    "tests/formal/test_phase20_native.c","tests/formal/run_phase20_native.py",
    "tests/formal/test_phase20_gates.py","tools/check_portability.py",
    "tests/formal/test_phase20_regressions.py","tests/formal/phase20_bytes_model_canary.mlw",
    "tests/formal/run_phase20_model_canary.py","machine/formal/phase20-model-blocker-v1.json",
    ".github/workflows/phase20-receipt-prerequisites.yml",
    "machine/formal/phase20-goals-v1.json",
    "machine/formal/phase20-provers-v1.json",
    "Makefile","src/core/deletion.c","tools/check_hacl_source.py",
    "vendor/hacl-star/SOURCES.json","vendor/hacl-star/UPSTREAM.md",
}
INPUTS |= {"vendor/hacl-star/"+path for path in
           json.loads((ROOT/"vendor/hacl-star/SOURCES.json").read_text())["git_blobs_sha1"]}

def load(path):
    return json.loads(Path(path).read_text(),object_pairs_hook=gate.unique_pairs)

def solver_logs(raw):
    """Extract every invocation through the end of its original JSON report.

    Only the GitHub timestamp prefix is removed. No reconstructed solver text,
    truncated report, parser failure or duplicate target is accepted.
    """
    text=re.sub(r"^\d{4}-\d\d-\d\dT\S+Z ","",raw,flags=re.M)
    parts=re.split(r"(?=^32\.1 \(Germanium\)\s*$)",text,flags=re.M)[1:]
    result={}
    for part in parts:
        start=re.search(r'(?m)^\[\s*\{\s*"goal"\s*:',part)
        if start is None:
            raise ValueError("original structured report is missing")
        _,end=json.JSONDecoder(object_pairs_hook=gate.unique_pairs).raw_decode(part[start.start():])
        log=part[:start.start()+end]+"\n"
        source=re.findall(r"\[kernel\] Parsing /repo/phase20-([^ ]+)\.c",log)
        function=re.findall(r"\[rte:annot\] annotating function (\w+)",log)
        if len(source) != 1 or len(function) != 1:
            raise ValueError("ambiguous original source or function")
        target=function[0] if source[0] == "receipt" else source[0]
        if target not in gate.TARGETS or target in result:
            raise ValueError("unknown or repeated retained target")
        result[target]=log
    if not result:
        raise ValueError("no original solver invocation")
    return result

def verified_log(row,root):
    path=Path(row["path"])
    if path.is_absolute() or ".." in path.parts or path.suffix != ".log":
        raise ValueError("invalid retained log path")
    raw=(root/path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != row["sha256"]:
        raise ValueError("retained original log changed")
    return raw.decode()

def validate(record,root=ROOT,require_complete=True):
    keys={"format","version","scope","head_sha","ci_checkout_sha","base_sha","run_id",
          "workflow_conclusion","workflow_failure","tool","solver_result","incomplete_targets",
          "canonical_json_theorem","actual_streaming_sha_provider","libc_implementation",
          "model_separation","original_phase18_global_frame","review","issue_28",
          "negative_controls","source_blobs","generated_sha256","solver_jobs","native_jobs",
          "diagnostic_jobs","failed_attempts"}
    if set(record) != keys or type(record["version"]) is not int:
        raise ValueError("unknown/missing evidence field or invalid version")
    if (record["format"],record["version"],record["scope"]) != (
        "tombstone.phase20.evidence",1,"CONDITIONAL_RECEIPT_VALIDATION_AND_FORMATTER_FRAME"):
        raise ValueError("wrong evidence kind or scope")
    if tuple(record[key] for key in ("head_sha","ci_checkout_sha","run_id","workflow_conclusion","workflow_failure")) != EXECUTION:
        raise ValueError("historical execution was relabelled")
    for key in ("head_sha","ci_checkout_sha","base_sha"):
        if not re.fullmatch(r"[0-9a-f]{40}",record[key]):
            raise ValueError("unresolved execution identity")
    if record["head_sha"] == record["ci_checkout_sha"]:
        raise ValueError("PR and merge-checkout identities conflated")
    if record["tool"] != {
        "version":"32.1","model":"Bytes","prover":"Alt-Ergo 2.5.4","rte":True,
        "formatter_options":["-wp-literals","-wp-no-callee-precond"],
        "hex_strategy":"wp:bitshift",
        "container":"framac/frama-c:32.1@sha256:4f0b7a2bd600c4daabfdcdfa393a3c18301e0db18f3b2739f1d9650193462d36",
    }:
        raise ValueError("tool/model/RTE identity changed")
    for key,value in {
        "canonical_json_theorem":"OPEN","actual_streaming_sha_provider":"OPEN",
        "libc_implementation":"ASSUMED","model_separation":"ASSUMED",
        "original_phase18_global_frame":"NOT_DISCHARGED",
        "review":"REQUIRED_ON_FINAL_EXACT_HEAD","issue_28":"OPEN",
    }.items():
        if record[key] != value:
            raise ValueError("unsupported claim promotion: "+key)
    if set(record["source_blobs"]) != INPUTS:
        raise ValueError("missing or unexpected proof dependency")
    for path,expected in record["source_blobs"].items():
        p=root/path
        if p.is_symlink() or overlay.bridge.p18.git_blob(p.read_bytes()) != expected:
            raise ValueError("stale proof dependency: "+path)
    inventory=load(root/"machine/formal/phase20-goals-v1.json")
    if set(inventory) != set(gate.TARGETS):
        raise ValueError("missing or unexpected proof target")
    found={}
    if len({row["job_id"] for row in record["solver_jobs"]}) != len(record["solver_jobs"]):
        raise ValueError("repeated solver job")
    for row in record["solver_jobs"]:
        raw=verified_log(row,root)
        if record["ci_checkout_sha"] not in raw:
            raise ValueError("original log checkout mismatch")
        for target,log in solver_logs(raw).items():
            if target in found:
                raise ValueError("duplicate target across jobs")
            generated=(overlay.render_hex(target[4:]) if target.startswith("hex-") else
                       overlay.mutant(target) if target in gate.NEGATIVE else overlay.render())
            digest=hashlib.sha256(generated.encode()).hexdigest()
            if record["generated_sha256"][target] != digest or digest not in raw:
                raise ValueError("generated source identity mismatch")
            result=gate.parse(log,target)
            if result != gate.inventory_entry(inventory[target]):
                raise ValueError("retained goal inventory or diagnostics changed")
            found[target]=result
    if set(found) != set(gate.TARGETS):
        raise ValueError("incomplete executed target set")
    incomplete=sorted(target for target,result in found.items()
                      if target not in gate.NEGATIVE and result["unproved"])
    expected_result="INCOMPLETE" if incomplete else "COMPLETE_UNDER_EXPLICIT_PREMISES"
    if record["solver_result"] != expected_result or record["incomplete_targets"] != incomplete:
        raise ValueError("unsupported solver-result promotion")
    for target in gate.NEGATIVE:
        suffix=gate.NEGATIVE[target]
        needle="bytes_"+gate.TARGETS[target]+("_" if suffix.startswith("ensures") else "_ensures_")+suffix
        if needle not in found[target]["unproved"]:
            raise ValueError("designated semantic obligation did not fail")
    controls={target:("BLOCKED_BY_POSITIVE_BASELINE" if gate.TARGETS[target] in incomplete
                       else "DESIGNATED_OBLIGATION_UNPROVED_AND_NATIVE_MUTANT_REJECTED")
              for target in gate.NEGATIVE}
    if record["negative_controls"] != controls:
        raise ValueError("unsupported negative-control promotion")
    expected={(cc,backend) for cc in ("gcc","clang") for backend in ("openssl","hacl")}
    native=record["native_jobs"]
    if len(native) != 4 or {(r["cc"],r["backend"]) for r in native} != expected:
        raise ValueError("missing native compiler/provider tuple")
    if len({row["job_id"] for row in native}) != 4:
        raise ValueError("repeated native job")
    for row in native:
        raw=verified_log(row,root)
        if row["conclusion"] != "success":
            raise ValueError("native execution did not pass")
        if record["ci_checkout_sha"] not in raw:
            raise ValueError("native checkout mismatch")
        if "run_phase20_native.py --cc "+row["cc"]+" --backend "+row["backend"] not in raw:
            raise ValueError("native command tuple mismatch")
        for message in ("PASS: 160 validator cases; 2530 formatter cases including 30 injected failures",
                        "PASS: native accept-invalid rejected specifically by VALIDATION_REJECT",
                        "PASS: native bad-size rejected specifically by FORMAT_SIZE",
                        "PASS: native error-size rejected specifically by ERROR_SIZE"):
            if message not in raw:
                raise ValueError("missing native semantic result")
    # Earlier parser errors and incomplete proofs never become positive proof.
    attempts={str(path.relative_to(root)) for path in (root/"machine/formal").glob("phase20-attempt-*.json")}
    if not attempts or set(record["failed_attempts"]) != attempts or len(record["failed_attempts"]) != len(attempts):
        raise ValueError("failed attempt inventory changed or omitted")
    for path in record["failed_attempts"]:
        attempt=load(root/path)
        if attempt["conclusion"] != "FAILED":
            raise ValueError("failed attempt was relabelled")
        for row in attempt["logs"]:
            verified_log(row,root)
    if require_complete and incomplete:
        raise ValueError("positive proof is incomplete: "+", ".join(incomplete))
    return incomplete

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--inspect-incomplete",action="store_true",
                        help="check retained evidence integrity without granting proof acceptance")
    args=parser.parse_args()
    try:
        incomplete=validate(load(RECORD),require_complete=not args.inspect_incomplete)
    except (ValueError,KeyError,TypeError,OSError) as error:
        raise SystemExit("FAIL: Phase 20 evidence: "+str(error)) from error
    if incomplete:
        print("INCOMPLETE: evidence integrity checked; proof acceptance BLOCKED: "+", ".join(incomplete))
    else:
        print("PASS: exact source, complete WP/RTE inventories, semantic controls and preserved original logs")
    print("LIMIT: conditional libc/provider/model premises; fresh exact-head review still required")
