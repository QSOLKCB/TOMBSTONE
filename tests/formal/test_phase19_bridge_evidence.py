#!/usr/bin/env python3
"""Reject stale provenance, omitted goals, and unsupported claim promotion."""
import copy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import check_phase19_bridge_evidence as evidence

record = evidence.load(evidence.RECORD)
evidence.validate(record)


def rejected(edit):
    changed = copy.deepcopy(record)
    edit(changed)
    try:
        evidence.validate(changed)
    except (ValueError, KeyError, OSError):
        return
    raise AssertionError("invalid bridge evidence accepted")


for field, value in [("original_phase18_global_frame", "DISCHARGED"),
                     ("actual_provider_refinement", "PROVED"), ("review", "APPROVED"),
                     ("issue_28", "CLOSED"), ("good_receipt", "PROVED"),
                     ("format_json", "PROVED"), ("libc_memcmp", "PROVED"),
                     ("model_block_separation", "PROVED"),
                     ("workflow_conclusion", "success"), ("version", True),
                     ("head_sha", record["ci_checkout_sha"])]:
    rejected(lambda r: r.__setitem__(field, value))
rejected(lambda r: r["source_blobs"].pop("tools/phase19_bridge_overlay.py"))
rejected(lambda r: r["source_blobs"].__setitem__("src/encoding/receipt.c", "0" * 40))
rejected(lambda r: r["solver_jobs"].pop())
rejected(lambda r: r["solver_jobs"][0].__setitem__("total", 0))
rejected(lambda r: r["solver_jobs"][0].__setitem__("sha256", "0" * 64))
rejected(lambda r: r["solver_jobs"][0].__setitem__("generated_sha256", "0" * 64))
rejected(lambda r: r["other_jobs"].pop())
rejected(lambda r: r["tool"].__setitem__("rte", False))
print("PASS: 19 stale, missing, relabelled and overclaimed bridge evidence controls")
