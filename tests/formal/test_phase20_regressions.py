#!/usr/bin/env python3
"""Replay the actual composition regression independently of stale snapshots."""
import copy
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_phase20_evidence as evidence
import check_phase20_wp as gate

old = evidence.solver_logs((ROOT / "formal/evidence/phase20/run-41365582954-job-125024927421.log").read_text())
new = evidence.solver_logs((ROOT / "formal/evidence/phase20/run-41367373120-job-125030295346.log").read_text())
# These location regressions deliberately replay historical original-model
# records. They neither renew evidence nor use the corrected-model inventory.
inventory = evidence.load(ROOT / "machine/formal/phase20-goals-v1.json")
checks = 0


def rejects(action):
    global checks
    try:
        action()
    except (ValueError, KeyError, TypeError):
        checks += 1
    else:
        raise AssertionError("changed proof evidence was accepted")


assert set(old) == set(new) == {"calculate_hash", "tb_receipt_verify_chain"}
for target in old:
    # These are original reports from before and after checked annotations
    # moved source lines. No inventory or report is regenerated for the test.
    assert gate.parse(old[target], target) == gate.parse(new[target], target)
    gate.validate(old[target], target, inventory)
    gate.validate(new[target], target, inventory)
    checks += 1
    log = new[target]
    rejects(lambda: gate.validate(log, target, None))
    rejects(lambda: gate.validate(log, target, {target: inventory[target]}))
    rejects(lambda: gate.validate(log + "\n[wp] Warning:\n  new premise\n", target, inventory))
    rejects(lambda: gate.validate(log.replace("Warning:", "Warning:\n  changed premise", 1), target, inventory))
    rejects(lambda: gate.validate(log.replace("/repo/phase20-receipt.c:", "/repo/unknown.c:"), target, inventory))
    rejects(lambda: gate.validate(log.replace("32.1 (Germanium)", "32.0 (Germanium)"), target, inventory))
    start = re.search(r'(?m)^\[\s*\{\s*"goal"\s*:', log).start()
    goals, end = json.JSONDecoder().raw_decode(log[start:])
    def revised(items):
        return log[:start] + json.dumps(items) + log[start+end:]
    rejects(lambda: gate.validate(revised(goals[:-1]), target, inventory))
    changed = copy.deepcopy(goals)
    changed[0]["goal"] += "_changed"
    rejects(lambda: gate.validate(revised(changed), target, inventory))

for name in ("receipt", "hex-openssl", "hex-hacl", "accept-invalid", "bad-size", "error-size"):
    warning = f"[wp] /repo/phase20-{name}.c:12: Warning:\n  preserved premise"
    moved = warning.replace(".c:12:", ".c:812:")
    assert gate.normalize_diagnostics([warning]) == gate.normalize_diagnostics([moved])
    assert gate.normalize_diagnostics([warning]) != gate.normalize_diagnostics([moved.replace("premise", "different premise")])
    checks += 1
outside = "[wp] /repo/other.c:12: Warning:\n  premise"
assert gate.normalize_diagnostics([outside]) != gate.normalize_diagnostics([outside.replace(":12:", ":13:")])
checks += 1
print(f"PASS: {checks} Phase 20 regressions; original composition reports replay, changed proof content rejected")
