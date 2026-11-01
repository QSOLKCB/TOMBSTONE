#!/usr/bin/env python3
"""Validate retained execution evidence; never infer current-head approval."""
import hashlib
import json
from pathlib import Path
import re

import check_phase19_bridge_log as gate
import phase19_bridge_overlay as overlay

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "machine/formal/phase19-bridge-evidence-v1.json"
EXPECTED = {"equal32": (11, 11), "calculate_hash": (51, 51),
            "tb_receipt_verify_chain": (62, 62), "missing-cleanup": (47, 48),
            "double-cleanup": (51, 53), "caller-corruption": (51, 55)}
INPUTS = {
    "src/encoding/receipt.c", "src/crypto/fingerprint.c", "src/crypto/fingerprint_hacl.c",
    "include/tombstone/receipt.h", "include/tombstone/fingerprint.h", "include/tombstone/deletion.h",
    "tools/phase18_wp_overlay.py", "tools/phase19_equal32_overlay.py",
    "tools/phase19_calculate_hash_overlay.py", "tools/phase19_hash_errors_overlay.py",
    "tools/phase19_bridge_overlay.py", "tools/phase19_bridge_native.py",
    "tests/formal/test_phase19_faults.c", "machine/formal/phase18-unbounded-wp-v1.json",
    "machine/examples/explicit-delete-v1.json", "machine/examples/observed-transition-v1.json",
    "machine/examples/unchanged-v1.json",
}


def load(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=gate.unique_pairs)


def solver_log(raw):
    lines = [re.sub(r"^\d{4}-\d\d-\d\dT\S+Z ", "", line) for line in raw.splitlines()]
    starts = [i for i, line in enumerate(lines) if line == "32.1 (Germanium)"]
    if len(starts) != 1:
        raise ValueError("ambiguous retained prover invocation")
    end = next((i for i in range(starts[0], len(lines))
                if lines[i].startswith(("PASS: ", "FAIL: ", "##[error]"))), len(lines))
    return "\n".join(lines[starts[0]:end]) + "\n"


def validate(record, root=ROOT):
    if (record["format"], record["version"], record["scope"]) != (
            "tombstone.phase19.bridge-evidence", 1, "CONDITIONAL_CALLER_FRAME_AND_CALL_PROTOCOL"):
        raise ValueError("wrong evidence kind or scope")
    if type(record["version"]) is not int or (
            record["head_sha"], record["ci_checkout_sha"], record["run_id"],
            record["workflow_conclusion"], record["workflow_failure"]) != (
            "dfcc419f8736d6095633e1d708d17519a72e623e",
            "3394270823845a23de2930c0a6d5b0ea3f1d6b89", 41353978018,
            "failure", "MULTILINE_JSON_REPORT_GATE"):
        raise ValueError("historical execution was relabelled")
    if record["original_phase18_global_frame"] != "NOT_DISCHARGED" or record["actual_provider_refinement"] != "OPEN":
        raise ValueError("unsupported global-frame/provider promotion")
    if record["review"] != "REQUIRED_ON_FINAL_EXACT_HEAD" or record["issue_28"] != "OPEN":
        raise ValueError("retained proof cannot grant review or close remaining obligations")
    for premise in ("good_receipt", "format_json", "libc_memcmp", "model_block_separation"):
        if record[premise] != "ASSUMED":
            raise ValueError("undischarged external premise promoted")
    if record["tool"] != {"name": "Frama-C/WP", "version": "32.1",
            "prover": "Alt-Ergo 2.5.4", "model": "Bytes", "rte": True,
            "container": "framac/frama-c:32.1@sha256:4f0b7a2bd600c4daabfdcdfa393a3c18301e0db18f3b2739f1d9650193462d36"}:
        raise ValueError("changed tool/model/RTE identity")
    if set(record["source_blobs"]) != INPUTS:
        raise ValueError("missing or unexpected source dependency")
    for path, expected in record["source_blobs"].items():
        p = root / path
        if p.is_symlink() or overlay.p18.git_blob(p.read_bytes()) != expected:
            raise ValueError("stale proof input: " + path)
    for key in ("head_sha", "ci_checkout_sha", "base_sha"):
        if not re.fullmatch(r"[0-9a-f]{40}", record[key]):
            raise ValueError("unresolved execution identity")
    if record["head_sha"] == record["ci_checkout_sha"]:
        raise ValueError("PR and merge-checkout identities were conflated")
    inventory = load(root / "machine/formal/phase19-bridge-goals-v1.json")
    diagnostics = load(root / "machine/formal/phase19-bridge-diagnostics-v1.json")
    if set(inventory) != set(gate.TARGETS):
        raise ValueError("missing proof target inventory")
    rows = record["solver_jobs"]
    if len(rows) != len(EXPECTED) or {row["target"] for row in rows} != set(EXPECTED):
        raise ValueError("missing or duplicate composition/control target")
    for row in rows:
        target = row["target"]
        if (row["proved"], row["total"]) != EXPECTED[target]:
            raise ValueError("changed proof count")
        path = Path(row["path"])
        if path.is_absolute() or ".." in path.parts or path.suffix != ".log":
            raise ValueError("invalid retained log path")
        raw = (root / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("retained original log changed")
        text = raw.decode()
        if record["ci_checkout_sha"] not in text:
            raise ValueError("retained log checkout mismatch")
        mutant = target if target in gate.NEGATIVE else None
        rendered = overlay.mutant(mutant) if mutant else overlay.render()
        generated_sha = hashlib.sha256(rendered.encode()).hexdigest()
        if row["generated_sha256"] != generated_sha or generated_sha not in text:
            raise ValueError("generated actual-source identity mismatch")
        counts = gate.validate(solver_log(text), "calculate_hash" if mutant else target,
                               mutant, inventory, diagnostics)
        if counts != EXPECTED[target]:
            raise ValueError("retained result disagrees with evidence")
    other = record["other_jobs"]
    if len(other) != 3 or {row["target"] for row in other} != {
            "native-gcc", "native-clang", "original-phase18-54-of-54"}:
        raise ValueError("missing native/original theorem evidence")
    for row in other:
        raw = (root / row["path"]).read_bytes()
        if row["conclusion"] != "success" or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("supporting execution changed")
        text = raw.decode()
        if row["target"].startswith("native-"):
            cc = row["target"].removeprefix("native-")
            for case in ("positive", *gate.NEGATIVE):
                if "PASS: " + cc + " " + case not in text:
                    raise ValueError("missing concrete control result")
        elif not re.search(r"\[wp\] Proved goals:\s*54 / 54", text):
            raise ValueError("original theorem did not rerun completely")
    # The deliberately failed first run remains a failure with intact raw logs.
    attempt = load(root / "machine/formal/phase19-bridge-attempt-1.json")
    if attempt["conclusion"] != "FAILED_EVIDENCE_GATE":
        raise ValueError("failed attempt was relabelled")
    for row in attempt["logs"]:
        if hashlib.sha256((root / row["path"]).read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("original failed log changed")


if __name__ == "__main__":
    try:
        validate(load(RECORD))
    except (ValueError, OSError, KeyError, TypeError) as error:
        raise SystemExit("FAIL: P19-03 evidence: " + str(error)) from error
    print("PASS: retained P19-03 source, 3 complete proofs, 3 semantic controls and original failed attempt")
    print("LIMIT: conditional caller-frame/protocol evidence; no current-head review or real-provider closure")
