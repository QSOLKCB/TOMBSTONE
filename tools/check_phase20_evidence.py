#!/usr/bin/env python3
"""Bind the current proof inputs to preserved, original executed WP reports."""
import hashlib
import json
from pathlib import Path
import re

import check_phase19_bridge_evidence as previous
import check_phase20_wp as gate
import phase20_receipt_overlay as overlay

ROOT=Path(__file__).resolve().parents[1]
RECORD=ROOT/"machine/formal/phase20-evidence-v1.json"
INPUTS=previous.INPUTS | {
    "tools/check_phase19_bridge_evidence.py","tools/check_phase19_bridge_log.py",
    "machine/formal/phase19-bridge-evidence-v1.json",
    "machine/formal/phase19-bridge-goals-v1.json","machine/formal/phase19-bridge-diagnostics-v1.json",
    "tools/phase20_receipt_overlay.py","tools/check_phase20_wp.py",
    "tools/check_phase20_evidence.py","tests/formal/test_phase20_overlay.py",
    "tests/formal/test_phase20_native.c","tests/formal/run_phase20_native.py",
    "tests/formal/test_phase20_gates.py","tools/check_portability.py",
    ".github/workflows/phase20-receipt-prerequisites.yml",
    "machine/formal/phase20-goals-v1.json",
}

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

def validate(record,root=ROOT):
    if (record["format"],record["version"],record["scope"]) != (
        "tombstone.phase20.evidence",1,"CONDITIONAL_RECEIPT_VALIDATION_AND_FORMATTER_FRAME"):
        raise ValueError("wrong evidence kind or scope")
    for key in ("head_sha","ci_checkout_sha","base_sha"):
        if not re.fullmatch(r"[0-9a-f]{40}",record[key]):
            raise ValueError("unresolved execution identity")
    if record["head_sha"] == record["ci_checkout_sha"]:
        raise ValueError("PR and merge-checkout identities conflated")
    if record["tool"] != {
        "version":"32.1","model":"Bytes","prover":"Alt-Ergo 2.5.4","rte":True,
        "container":"framac/frama-c:32.1@sha256:4f0b7a2bd600c4daabfdcdfa393a3c18301e0db18f3b2739f1d9650193462d36",
    }:
        raise ValueError("tool/model/RTE identity changed")
    for key,value in {
        "solver_result":"COMPLETE_UNDER_EXPLICIT_PREMISES",
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
            found[target]=gate.validate(log,target,inventory)
    if set(found) != set(gate.TARGETS):
        raise ValueError("incomplete executed target set")
    expected={(cc,backend) for cc in ("gcc","clang") for backend in ("openssl","hacl")}
    native=record["native_jobs"]
    if len(native) != 4 or {(r["cc"],r["backend"]) for r in native} != expected:
        raise ValueError("missing native compiler/provider tuple")
    for row in native:
        raw=verified_log(row,root)
        if row["conclusion"] != "success":
            raise ValueError("native execution did not pass")
        if record["ci_checkout_sha"] not in raw:
            raise ValueError("native checkout mismatch")
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

if __name__ == "__main__":
    try:
        validate(load(RECORD))
    except (ValueError,KeyError,TypeError,OSError) as error:
        raise SystemExit("FAIL: Phase 20 evidence: "+str(error)) from error
    print("PASS: exact source, complete WP/RTE inventories, semantic controls and preserved original logs")
    print("LIMIT: conditional libc/provider/model premises; fresh exact-head review still required")
