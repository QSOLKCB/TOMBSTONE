#!/usr/bin/env python3
"""Phase 19: imported exact-head conditional proof receipt integrity gate.

This does not authenticate provider GitHub execution nor upgrade old evidence
to the current PR head. All current-head source and CI tests still must pass.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"machine/formal/phase19-helper-evidence-v1.json"
BLOBS={
"src/encoding/receipt.c":"6fe3e8014e9c38ea42c43b9133f026967a4158e3",
"tools/phase19_equal32_overlay.py":"f5e3df395de2d7aff3a91c8c6566427721033eca",
"tools/phase19_calculate_hash_overlay.py":"96441be54854339ae54ce104009d4ddb8a68164d",
}
EXPECTED=[("equal32",11,124973534748),("calculate_hash",40,124973534915)]

def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def pairs(items):
    out={}
    for k,v in items:
        if k in out:raise ValueError("duplicate evidence field "+k)
        out[k]=v
    return out

def read(path=PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"),object_pairs_hook=pairs,
                      parse_constant=lambda _:(_ for _ in ()).throw(ValueError("nonfinite")))

def verify(e,root=ROOT):
    assert e["format"]=="tombstone.phase19.helper-wp-evidence"
    assert type(e["phase"]) is int and e["phase"]==19
    assert type(e["version"]) is int and e["version"]==1
    s=e["source"]
    assert s["path"]=="src/encoding/receipt.c"
    assert s["git_blob_sha"]==BLOBS[s["path"]]
    assert s["source_main_commit"]=="8b4c87899c18524eb1ce3f6e89641504caff67cf"
    run=e["reported_execution"]
    assert run["pr_head_sha"]=="b62384ef6a86f2a50981dbe20c37e49f6a9f7982"
    assert run["ci_checkout_sha"]=="2cc0e2a300b98213ecc56fc170975ec96894bb7a"
    assert run["workflow_run_id"]==41348552076
    assert run["workflow_url"]=="https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41348552076"
    assert run["class"]=="provider-CI-executed-not-independent-replay"
    assert run["tool"]=="Frama-C/WP 32.1" and run["prover"]=="Alt-Ergo 2.5.4"
    assert run["rte_enabled"] is True and run["memory_model"]=="Bytes"
    assert len(e["targets"])==2
    for item,(name,total,job) in zip(e["targets"],EXPECTED):
        assert item["function"]==name and item["job_id"]==job
        assert type(item["goal_count"]) is int and item["goal_count"]==total
        assert type(item["proved"]) is int and item["proved"]==total
        assert item["status"]=="PASS_CONDITIONAL"
        assert len(item["external_assumptions"])>=2
        assert item["overlay_git_blob_sha"]==BLOBS[item["overlay_path"]]
    for name,expected in BLOBS.items():
        f=Path(root)/name
        assert f.is_file() and not f.is_symlink()
        assert blob(f.read_bytes())==expected, "stale input "+name
    assert e["native"]["status"]=="PASS" and e["native"]["compilers"]==["gcc","clang"]
    assert [x["id"] for x in e["residual"]]==["P19-03","A04","A05"]
    assert all(x["status"] in ("OPEN","NOT_PROVED") for x in e["residual"])
    assert "assigns out-only" in e["residual"][0]["scope"]
    assert e["promotion"]=="PROOF_SCOPED_CONDITIONAL_ONLY_BRIDGE_BLOCKED"
    assert len(e["rejected_attempts"])==2
    assert e["rejected_attempts"][0]["proved"]==13
    assert e["rejected_attempts"][1]["proved"]==37
    assert len(e["excluded_claims"])>=5
    assert e["release"]=={"tag":"v0.1.0","modified":False}

if __name__=="__main__":
    try:verify(read())
    except (AssertionError,ValueError,TypeError,KeyError,OSError) as error:
        raise SystemExit("FAIL: Phase 19 scoped-proof receipt: "+str(error)) from error
    print("PASS: actual-source helper WP proof receipt 11/11 + 40/40 is source-pinned, conditional, and bridge-blocked")
    print("LIMIT: this is a prior exact-run record, not provider correctness or new-head proof")
