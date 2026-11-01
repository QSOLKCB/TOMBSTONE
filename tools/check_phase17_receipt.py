#!/usr/bin/env python3
"""Fail-closed provenance record gate for executed bounded Phase 17 evidence.

A recorded CI result is an audit pointer, NOT a substitute for rerunning the
verification on the exact current head. No independent network claims.
"""
import json
from pathlib import Path

from check_phase17_evidence import BLOBS, git_blob, ROOT

RECEIPT = ROOT / "machine/formal/phase17-chain-evidence-v1.json"
SOURCE = "src/encoding/receipt.c"
OVERLAY = "formal/cbmc/chain_v17_harness.c"
RUNTIME = "tests/formal/test_chain_v17.c"
CASES = [
    ("check_null_and_empty", 843),
    ("check_genesis_nonzero", 843),
    ("check_oversized_count", 843),
]
RUN = 41333210346
HEAD = "5079d73c5506b05f30b2030c47d99b0a0e8bf5db"

def verify(record: dict) -> None:
    assert isinstance(record, dict)
    assert record["format"] == "tombstone.formal-proof-evidence"
    assert record["version"] == 1 and record["phase"] == 17
    assert record["scope"] == "actual-source-public-chain-verifier-prehash-rejection-only"
    assert record["checker"] == "CBMC" and record["checker_version"] == "6.11.0"
    for name, path_key, sha_key in [
        (SOURCE, "source_path", "source_git_blob_sha"),
        (OVERLAY, "overlay_path", "overlay_git_blob_sha"),
        (RUNTIME, "runtime_path", "runtime_git_blob_sha"),
    ]:
        assert record[path_key] == name
        assert record[sha_key] == BLOBS[name]
        assert git_blob((ROOT / name).read_bytes()) == record[sha_key]
    assert record["frozen_fixture_git_blobs"] == {
        name: BLOBS[name] for name in BLOBS if name.startswith("machine/examples/")
    }
    assert record["github_run_id"] == RUN and record["checked_commit_sha"] == HEAD
    assert record["run_url"] == "https://github.com/QSOLKCB/TOMBSTONE/actions/runs/" + str(RUN)
    assert record["checks"] == [
        {"function": function, "total_properties": total, "failed_properties": 0}
        for function, total in CASES
    ]
    assert record["total_properties"] == sum(p for _, p in CASES) == 2529
    assert record["failed_properties"] == 0
    assert record["model"] == {
        "input_scope": "NULL/zero/oversized count and nonzero genesis prehash status paths",
        "unwinding_assertions": True,
        "bounds_check": True,
        "pointer_check": True,
        "signed_overflow_check": True,
        "unsigned_overflow_check": True,
        "unwind": 96,
    }
    assert record["native_matrix"] == {
        "arches": ["x86_64", "aarch64"],
        "compilers": ["gcc", "clang"],
        "backends": ["openssl", "hacl"],
        "passed_jobs": 8,
        "executed_against_real_hash_providers": True,
    }
    assert record["release_boundary"] == {"tag": "v0.1.0", "modified": False}
    assert len(record["assumptions"]) >= 3
    assert len(record["excluded_claims"]) >= 4
    assert any("No full unbounded" in claim for claim in record["excluded_claims"])

def main() -> None:
    record = json.loads(RECEIPT.read_text(encoding="utf-8"))
    verify(record)
    print("PASS: Phase 17 2,529/2,529 executed bounded checks recorded with exact Git blobs and CI run")
    print("LIMIT: prior executed receipt does not replace mandatory current-head CI or prove full chain")

if __name__ == "__main__":
    main()
