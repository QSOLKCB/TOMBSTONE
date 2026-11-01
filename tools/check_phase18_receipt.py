#!/usr/bin/env python3
"""Fail-closed provenance gate for a *previously executed* Phase 18 WP result.

This checks proof receipt identity and conditional scope; it never turns a
prior run into current-head verification or proves external SHA assumptions.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"machine/formal/phase18-unbounded-wp-v1.json"
EXPECTED={
    "src/encoding/receipt.c": "6fe3e8014e9c38ea42c43b9133f026967a4158e3",
    "tools/phase18_wp_overlay.py": "b5efcbe605f8a33d2eea9f6d412f320198aff759",
    "tools/check_phase18_wp_log.py": "d467838d8ff0179b714636846f63870863f7922d",
}
EXCLUSIONS={
    "No proof of SHA-256, OpenSSL, HACL* or true digest value",
    "No proof of full canonical receipt parser or JSON encoder or hash-domain refinement",
    "No assertion of independent anchor custody, authorship, timestamps, real deletion or physical erasure",
    "No proof of GCC, Clang, Rust, system libraries, kernel, firmware or hardware",
    "Null/invalid-count argument paths are separately covered by Phase 17 and not within Phase 18 valid-input contract",
}

def blob(value:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(value)).encode("ascii")+b"\0"+value).hexdigest()

def pairs(values):
    out={}
    for k,v in values:
        if k in out: raise ValueError("duplicate proof field")
        out[k]=v
    return out

def load(path=PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"),object_pairs_hook=pairs)

def validate(record:dict,root=ROOT)->None:
    assert record["format"]=="tombstone.phase18.modular-wp-evidence"
    assert type(record["version"]) is int and record["version"]==1
    assert type(record["phase"]) is int and record["phase"]==18
    assert record["scope"]=="unbounded-valid-nonempty-public-C99-chain-loop-under-assumed-calculate_hash-and-equal32"
    assert record["checked_commit_sha"]=="a22c9dc00a74389720b88ef7ee05f18f82ca4848"
    assert record["github_run_id"]==41334542042 and record["job_id"]==124931454486
    assert record["run_url"]=="https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41334542042"
    for field,path in [("source","src/encoding/receipt.c"),("overlay_generator","tools/phase18_wp_overlay.py"),("wp_log_gate","tools/check_phase18_wp_log.py")]:
        entry=record[field]
        assert entry["path"]==path
        assert entry["git_blob_sha"]==EXPECTED[path]
        f=Path(root)/path
        assert f.is_file() and not f.is_symlink()
        assert blob(f.read_bytes())==EXPECTED[path]
    assert "strip the four generated ACSL annotations" in record["overlay_generator"]["byte_identity"]
    checker=record["checker"]
    assert checker=={
        "name":"Frama-C/WP","version":"32.1",
        "provers":{"Qed":38,"Alt-Ergo 2.5.4":16},
        "proved":54,"total":54,
        "wp_rte":True,"model":"Bytes",
        "function":"tb_receipt_verify_chain","unbounded":True
    }
    assert len(record["preconditions"])==4
    assert "count >= 1" in record["preconditions"][0]
    assert len(record["conclusions"])==4
    assert len(record["assumptions"])==3
    assert any("NOT separately proved" in s for s in record["assumptions"])
    assert any("no correctness" in s for s in record["assumptions"])
    assert set(record["exclusions"])==EXCLUSIONS
    assert record["release"]=={"tag":"v0.1.0","changed":False}

def main():
    try: validate(load())
    except (AssertionError,KeyError,ValueError,TypeError,OSError) as e:
        raise SystemExit("FAIL: Phase 18 source/assumption/proof receipt integrity: "+str(e)) from e
    print("PASS: 54/54 conditional unbounded WP proof receipt pinned to exact source, checkers, CI job")
    print("LIMIT: prior evidence does not prove a new commit or the actual SHA-256 provider")

if __name__=="__main__":
    main()
