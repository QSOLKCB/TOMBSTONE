#!/usr/bin/env python3
"""Negative controls for machine-readable Phase 17 bounded proof receipt."""
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_phase17_receipt as gate  # noqa: E402

record = json.loads(gate.RECEIPT.read_text(encoding="utf-8"))
gate.verify(record)

def fail(modifier, label: str):
    candidate = copy.deepcopy(record)
    modifier(candidate)
    try:
        gate.verify(candidate)
    except (AssertionError, KeyError, TypeError):
        return
    raise AssertionError("invalid Phase 17 proof receipt accepted: " + label)

fail(lambda x: x.update(total_properties=0), "zero/vacuous goals")
fail(lambda x: x.update(failed_properties=1), "failed proof falsely reported green")
fail(lambda x: x["checks"][1].update(total_properties=842), "changed function count")
fail(lambda x: x["checks"][1].update(failed_properties=1), "one failing property")
fail(lambda x: x.update(source_git_blob_sha="0" * 40), "stale C99 source")
fail(lambda x: x.update(overlay_git_blob_sha="0" * 40), "stale proof harness")
fail(lambda x: x["frozen_fixture_git_blobs"].update({
    "machine/examples/unchanged-v1.json": "0" * 40
}), "rewritten historical fixture")
fail(lambda x: x["model"].update(unwinding_assertions=False), "disabled unwinding")
fail(lambda x: x.update(checked_commit_sha="0" * 40), "wrong executed SHA")
fail(lambda x: x.update(github_run_id=0), "invented CI run")
fail(lambda x: x.update(phase=14), "incorrect phase claim")
fail(lambda x: x["native_matrix"].update(passed_jobs=0), "incomplete target matrix")
print("PASS: 12 corrupt, partial, vacuous or stale proof receipt variants fail closed")
