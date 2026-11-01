#!/usr/bin/env python3
"""Check executed Phase 11 and bounded Phase 13 evidence source identities.
Does NOT independently prove properties or validate remote Actions results.
"""
import json
import pathlib
import subprocess

root = pathlib.Path(__file__).resolve().parent.parent
record = json.loads((root / "machine/formal/phase11-wp-evidence-v1.json").read_text())
assert record["format"] == "tombstone.formal-proof-evidence"
assert record["version"] == 1 and record["phase"] == 11
for key in ("source", "overlay"):
    p = root / record[key + "_path"]
    assert p.is_file(), f"missing proof input: {p}"
    actual = subprocess.check_output(["git", "hash-object", str(p)], cwd=root, text=True).strip()
    assert actual == record[key + "_git_blob_sha"], (
        f"{key} changed without a new executed proof; expected "
        f"{record[key + '_git_blob_sha']}, observed {actual}"
    )
goals = record["goals"]
assert {g["function"] for g in goals} == {"fingerprints", "witness_stage", "tb_witness_delete"}
assert all(isinstance(g["proved"], int) and g["total"] > 0 and
           g["proved"] == g["total"] for g in goals)
assert sum(g["proved"] for g in goals) == record["total_proved"] == record["total_goals"] == 88
assert record["wp_rte_enabled"] is True
assert record["assumptions"] and record["excluded_claims"]
print("PASS: Phase 11 proof source/overlay blob identity and 88-goal receipt are consistent")
print("NOTE: Source identity check is not proof of Actions execution or external SHA provider.")

phase13 = json.loads((root / "machine/formal/phase13-adapter-cbmc-v1.json").read_text())
assert phase13["format"] == "tombstone.formal-proof-evidence"
assert phase13["phase"] == 13 and phase13["version"] == 1
assert phase13["checker"] == "CBMC" and phase13["checker_version"] == "6.11.0"
assert phase13["total_properties"] == 584 and phase13["failed_properties"] == 0
assert phase13["checks"] == [
    {"function": "check_one_shot", "failed": 0, "total": 195},
    {"function": "check_stream", "failed": 0, "total": 195},
    {"function": "check_invalid", "failed": 0, "total": 194},
]
assert phase13["assumptions"] and phase13["excluded_claims"]
assert "13" in phase13["run_url"] and phase13["github_run_id"] == 41321354704
for key in ("source", "overlay"):
    p = root / phase13[key + "_path"]
    assert p.is_file(), f"missing Phase 13 proof input: {p}"
    actual = subprocess.check_output(["git", "hash-object", str(p)], cwd=root, text=True).strip()
    assert actual == phase13[key + "_git_blob_sha"], (
        f"Phase 13 {key} changed without a newly executed CBMC run; "
        f"expected {phase13[key + '_git_blob_sha']}, observed {actual}"
    )
print("PASS: Phase 13 source and bounded-CBMC harness pinned to 584/584 executed property results")
print("NOTE: CBMC models the HACL boundary; not an SHA correctness or compiler proof.")
