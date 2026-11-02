#!/usr/bin/env python3
"""Validate retained original model-regression outputs, not just PASS strings."""
import hashlib
import json
from pathlib import Path
import re
import sys

import phase20_model as model
import phase20_receipt_overlay as overlay
from check_phase19_bridge_log import unique_pairs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests/formal"))
import run_phase20_model_canary as canary


def identity(text, build):
    for label, value in (("SPEC", build["spec_sha256"]), ("PLUGIN", build["plugin_sha256"])):
        found = re.findall(r"(?m)^PHASE20_MODEL_" + label + r"_SHA256=([0-9a-f]{64})$", text)
        if found != [value]:
            raise ValueError("missing, duplicate or different corrected model identity: " + label)


def validate(record, root=ROOT):
    if set(record) != {"directory", "files", "artifact_id", "archive_sha256"}:
        raise ValueError("unknown or missing model artifact field")
    if type(record["artifact_id"]) is not int or record["artifact_id"] <= 0 or not re.fullmatch(r"[0-9a-f]{64}", record["archive_sha256"]):
        raise ValueError("invalid original model artifact identity")
    directory = Path(record["directory"])
    if directory.is_absolute() or ".." in directory.parts or not str(directory).startswith("formal/evidence/phase20/"):
        raise ValueError("invalid model evidence directory")
    directory = root / directory
    files = {str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file()}
    if files != set(record["files"]):
        raise ValueError("missing or unexpected retained model file")
    for name, expected in record["files"].items():
        path = directory / name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("retained model output changed: " + name)
    report = json.loads((directory / "result.json").read_text(), object_pairs_hook=unique_pairs)
    if set(report) != {"format", "version", "build", "outcomes", "status"} or type(report["version"]) is not int:
        raise ValueError("unknown or missing model result field")
    if (report["format"], report["version"], report["status"]) != (
        "tombstone.phase20.corrected-model-regressions", 1, "CANARY_PASSED_NOT_A_SOUNDNESS_PROOF"):
        raise ValueError("incomplete or promoted model-regression status")
    build = report["build"]
    if build["spec_sha256"] != model.digest(model.SPEC) or not re.fullmatch(r"[0-9a-f]{64}", build["plugin_sha256"]):
        raise ValueError("unreviewed model correction identity")
    for name, hashes in model.spec()["files"].items():
        if name.startswith("share/") and build["share_sha256"].get(name) != hashes["corrected"]:
            raise ValueError("wrong corrected theory in model build")
    if (directory / "why3-version.log").read_text().strip() != "Why3 platform, version 1.8.2":
        raise ValueError("wrong retained Why3 version")
    if (directory / "alt-ergo-version.log").read_text().strip() != "v2.5.4":
        raise ValueError("wrong retained Alt-Ergo version")
    outcomes = report["outcomes"]
    if set(outcomes) != {"original", "corrected", "copy_regressions", "library_lemmas", "readonly", "string_lemma"}:
        raise ValueError("missing model or ghost-lemma regression")
    canary.require_results(outcomes["original"], canary.CONTROLS | canary.NEGATIVES)
    canary.require_results(outcomes["corrected"], canary.CONTROLS, canary.NEGATIVES)
    canary.require_results(outcomes["copy_regressions"], canary.EXTRAS)
    lemmas = {f"{endian}/read_{family}{bits}_copy_sep"
              for endian in ("le", "be") for family in ("uint", "sint", "init") for bits in (8, 16, 32, 64)}
    if set(outcomes["library_lemmas"]) != lemmas:
        raise ValueError("missing affected library lemma")
    for name, values in outcomes["library_lemmas"].items():
        goal = name.split("/")[1]
        canary.require_results(values, {goal, goal + "1"})

    def solver_outputs(folder, values):
        logs = list((directory / folder / "tasks").glob("*.log"))
        indexed = {p.stem.rsplit("-", 1)[-1]: p for p in logs}
        if len(logs) != len(indexed) or set(indexed) != set(values):
            raise ValueError("missing or duplicate original solver output")
        for name, status in values.items():
            text = indexed[name].read_text()
            if re.search(r"\b(error|exception|fatal)\b", text, re.I):
                raise ValueError("tool error in model evidence")
            valid = len(re.findall(r"\bValid \(", text)) == 1 and re.findall(r"(?m)^unsat$", text) == ["unsat"]
            if valid != (status == "VALID"):
                raise ValueError("model status disagrees with original solver output")
            if not valid and not re.search(r"(?m)^(timeout|sat|unknown)$", text):
                raise ValueError("unrecognized negative model evidence")

    for name, folder in (("original", "original"), ("corrected", "corrected"),
                         ("copy_regressions", "copy-regressions")):
        solver_outputs(folder, outcomes[name])
    for name, values in outcomes["library_lemmas"].items():
        solver_outputs("lemmas/" + name, values)

    readonly = {"ensures_const_readable", "ensures_const_not_writable", "ensures_ordinary_writable",
                "assert_literal_readable", "assert_literal_not_writable", "assigns"}
    for probe, function, expected, designated, automatic in (
        ("readonly", "readonly_model_probe", readonly, "assert_literal_not_writable", 2),
        ("string-lemma", "p20_string_witness", {"ensures", "assigns"}, "ensures", 2),
    ):
        for kind in ("positive", "negative"):
            data = outcomes[probe.replace("-", "_")][kind]
            values = data["goals"] if probe == "string-lemma" else data
            negatives = {designated} if kind == "negative" else set()
            canary.require_results(values, expected - negatives, negatives)
            folder = directory / (probe + "-" + kind)
            text = (folder / "frama-c.log").read_text()
            identity(text, build)
            if re.findall(r"\[rte:annot\] annotating function (\w+)", text) != [function]:
                raise ValueError("missing model/lemma RTE target")
            rows = json.loads((folder / "report.json").read_text(), object_pairs_hook=unique_pairs)
            if len(rows) != len(expected) or {r["goal"] for r in rows} != {"bytes_" + function + "_" + k for k in expected}:
                raise ValueError("changed original model/lemma goal inventory")
            for row in rows:
                name = row["goal"].removeprefix("bytes_" + function + "_")
                if (row["function"] != function or row["smoke"] is not False or not row["provers"]
                        or row["verdict"] not in ("valid", "timeout", "unknown", "stepout")
                        or row["passed"] is not (row["verdict"] == "valid")
                        or row["passed"] != (values[name] == "VALID")
                        or any(p["prover"] not in ("qed", "Alt-Ergo:2.5.4") for p in row["provers"])
                        or any(p["success"] not in (0, 1) for p in row["provers"])
                        or any(p["success"] for p in row["provers"]) != row["passed"]):
                    raise ValueError("unexecuted or inconsistent model/lemma verdict")
            expected_summary = (str(sum(r["passed"] for r in rows) + automatic), str(len(rows) + automatic))
            if re.findall(r"Proved goals:\s*(\d+)\s*/\s*(\d+)", text) != [expected_summary]:
                raise ValueError("model/lemma summary disagrees with individual goals")
            if probe == "string-lemma":
                source = overlay.render()
                if kind == "negative":
                    source = source.replace(overlay.STRING_LEMMA,
                        overlay.STRING_LEMMA.replace("  requires s[k] == '\\0';\n", "", 1), 1)
                if hashlib.sha256(source.encode()).hexdigest() != data["source_sha256"]:
                    raise ValueError("ghost lemma was not proved on the current overlay")
    return build
