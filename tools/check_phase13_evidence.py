#!/usr/bin/env python3
"""Phase 13 evidence/source binding. This does NOT rerun F* or prove machine code."""
from pathlib import Path
import json
import subprocess

root=Path(__file__).resolve().parent.parent
record=json.loads((root/"machine/formal/phase13-hacl-evidence-v1.json").read_text())
assert record["format"]=="tombstone.formal-integration-evidence"
assert record["phase"]==13 and record["version"]==1
assert record["upstream"]["verified_upstream_files"]==16
for name,expected in record["c99_source_blobs"].items():
    file=root/name
    assert file.is_file(),f"missing Phase 13 proof input {name}"
    actual=subprocess.check_output(["git","hash-object",str(file)],cwd=root,text=True).strip()
    assert actual==expected,f"stale Phase 13 evidence for {name}: {actual}"
matrix=record["toolchain_matrix"]
assert {(item["compiler"],item["os"]) for item in matrix}=={
    ("gcc","ubuntu-24.04"),("clang","ubuntu-24.04"),
    ("gcc","ubuntu-24.04-arm"),("clang","ubuntu-24.04-arm")}
assert all(item["status"]=="success" for item in matrix)
targets=record["cbmc"]["targets"]
assert {g["function"] for g in targets}=={"check_one_shot","check_stream","check_invalid"}
assert all(g["failures"]==0 and g["properties"]>0 for g in targets)
assert record["limitations"] and record["review_required"] is True
print("PASS: Phase 13 executed evidence and pinned adapter/harness source identities agree")
print("LIMIT: source/metadata checks do NOT replace upstream F* verification or adapter refinement")
