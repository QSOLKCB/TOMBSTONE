#!/usr/bin/env python3
"""Check Phase 11 evidence is pinned to the actual C99 and ACSL file blobs.
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
