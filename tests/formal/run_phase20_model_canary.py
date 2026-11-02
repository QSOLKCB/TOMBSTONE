#!/usr/bin/env python3
"""Reject inconsistent models and replay affected library lemmas.

Timeouts are permitted ONLY for explicitly false negative controls. Every
positive, refutation and library lemma must be VALID. This is regression
evidence, not a general proof of soundness of Frama-C, Why3 or Alt-Ergo.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import phase20_model as model
import phase20_receipt_overlay as overlay

CONTROLS = {"destination_before", "source_before", "neighbour_is_separate", "library_frame_value"}
NEGATIVES = {"definition_value", "contradictory_values"}
EXTRAS = {"signed_unsigned_copy", "copied_nonzero_offset", "before_untouched",
          "after_untouched", "copied_byte_is_not_zero", "wrong_value_refuted", "contradiction_refuted"}


def run(command, log, timeout=90):
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=timeout)
    log.write_text(result.stdout)
    return result


def verdict(result):
    if re.search(r"\b(error|exception|fatal)\b", result.stdout, re.I):
        raise ValueError("solver error")
    valid = len(re.findall(r"\bValid \(", result.stdout)) == 1
    if result.returncode == 0 and valid and re.findall(r"(?m)^unsat$", result.stdout) == ["unsat"]:
        return "VALID"
    if valid or re.search(r"(?m)^unsat$", result.stdout):
        raise ValueError("inconsistent solver response")
    if result.returncode == 142 and re.search(r"(?m)^timeout$", result.stdout):
        return "TIMEOUT_NOT_PROVED"
    if result.returncode == 0 and re.search(r"(?m)^(sat|unknown)$", result.stdout):
        return "NOT_PROVED"
    raise ValueError("unrecognized solver exit or result")


def require_results(outcomes, positives, negatives=frozenset()):
    if not set(outcomes.values()) <= {"VALID", "NOT_PROVED", "TIMEOUT_NOT_PROVED"}:
        raise ValueError("unrecognized model verdict")
    if set(outcomes) != positives | negatives:
        raise ValueError("missing, duplicate or unexpected goal inventory")
    if any(outcomes[name] != "VALID" for name in positives):
        raise ValueError("positive model obligation did not pass")
    if any(outcomes[name] == "VALID" for name in negatives):
        raise ValueError("Bytes theory proves a false claim; proof acceptance blocked")


def export(args, directory, share, source, options=()):
    directory.mkdir(parents=True)
    tasks = directory / "tasks"
    tasks.mkdir()
    command = [args.why3, "prove"]
    if args.config:
        command += ["--config", str(args.config)]
    command += ["-L", str(share / "why3"), "-P", "Alt-Ergo,2.5.4,",
                "-o", str(tasks), str(source), *options]
    result = run(command, directory / "export.log")
    if result.returncode:
        raise ValueError("Why3 task export failed: " + str(directory))
    files = sorted(tasks.glob("*.psmt2"))
    if not files:
        raise ValueError("no exported model obligations")
    return files


def solve(args, paths):
    outcomes = {}
    for path in paths:
        name = path.stem.rsplit("-", 1)[-1]
        if name in outcomes:
            raise ValueError("duplicate exported goal")
        result = run([args.alt_ergo, "--frontend", "dolmen", "--timelimit", "10", str(path)],
                     path.with_suffix(".log"))
        outcomes[name] = verdict(result)
    return outcomes


def readonly(args):
    outcomes = {}
    for kind in ("positive", "negative"):
        directory = args.output / ("readonly-" + kind)
        directory.mkdir()
        source = directory / "readonly.c"
        text = (HERE / "phase20_model_readonly.c").read_text()
        if kind == "negative":
            text = text.replace("literal_not_writable: !\\valid", "literal_not_writable: \\valid")
        source.write_text(text)
        report = directory / "report.json"
        command = [sys.executable, str(ROOT / "tools/phase20_model.py"), "run",
                   "--output", str(args.model), "--", "-wp", "-wp-literals", "-wp-rte",
                   "-wp-model", "Bytes", "-wp-fct", "readonly_model_probe",
                   "-wp-prover", "alt-ergo", "-wp-timeout", "10",
                   "-wp-report-json", str(report), str(source)]
        result = run(command, directory / "frama-c.log", timeout=180)
        if result.returncode or re.search(r"\[(?:.*error|.*abort).*\]", result.stdout, re.I):
            raise ValueError("readonly probe tool failure")
        rows = json.loads(report.read_text())
        for row in rows:
            if (row["function"] != "readonly_model_probe" or row["smoke"] is not False
                    or row["verdict"] not in ("valid", "unknown", "timeout", "stepout")
                    or row["passed"] is not (row["verdict"] == "valid")
                    or not row["provers"]
                    or any(p["prover"] not in ("qed", "Alt-Ergo:2.5.4") for p in row["provers"])
                    or any(p["success"] not in (0, 1) for p in row["provers"])
                    or any(p["success"] for p in row["provers"]) != row["passed"]):
                raise ValueError("unexecuted or inconsistent readonly proof")
        expected = {"ensures_const_readable", "ensures_const_not_writable", "ensures_ordinary_writable",
                    "assert_literal_readable", "assert_literal_not_writable", "assigns"}
        values = {row["goal"].removeprefix("bytes_readonly_model_probe_"):
                  "VALID" if row["verdict"] == "valid" and row["passed"] else "NOT_PROVED"
                  for row in rows}
        if len(rows) != len(values):
            raise ValueError("duplicate readonly goal")
        negatives = {"assert_literal_not_writable"} if kind == "negative" else set()
        require_results(values, expected - negatives, negatives)
        outcomes[kind] = values
    return outcomes


def string_lemma(args):
    """Prove the exact ghost helper used by the actual-source overlay.

    Its contract is not an external assumption: removing the NUL premise
    must make the ensures obligation fail on the same empty ghost body.
    """
    outcomes = {}
    for kind in ("positive", "negative"):
        directory = args.output / ("string-lemma-" + kind)
        directory.mkdir()
        source = directory / "phase20-receipt.c"
        text = overlay.render()
        if kind == "negative":
            altered = overlay.STRING_LEMMA.replace("  requires s[k] == '\\0';\n", "", 1)
            if altered == overlay.STRING_LEMMA:
                raise ValueError("string-lemma mutation did not apply")
            text = text.replace(overlay.STRING_LEMMA, altered, 1)
        source.write_text(text)
        report = directory / "report.json"
        result = run([sys.executable, str(ROOT / "tools/phase20_model.py"), "run",
                      "--output", str(args.model), "--", "-wp", "-wp-rte", "-wp-model", "Bytes",
                      "-wp-fct", "p20_string_witness", "-wp-prover", "alt-ergo", "-wp-timeout", "10",
                      "-wp-report-json", str(report), "-cpp-extra-args=-I" + str(ROOT / "include"),
                      str(source)], directory / "frama-c.log", timeout=180)
        if result.returncode or "[rte:annot] annotating function p20_string_witness" not in result.stdout:
            raise ValueError("string-lemma tool failure or missing RTE")
        rows = json.loads(report.read_text())
        if len(rows) != 2 or {r["goal"] for r in rows} != {
            "bytes_p20_string_witness_ensures", "bytes_p20_string_witness_assigns"}:
            raise ValueError("changed string-lemma goal inventory")
        values = {}
        for row in rows:
            if (row["function"] != "p20_string_witness" or row["smoke"] is not False
                    or row["verdict"] not in ("valid", "unknown", "timeout", "stepout")
                    or row["passed"] is not (row["verdict"] == "valid") or not row["provers"]
                    or any(p["prover"] not in ("qed", "Alt-Ergo:2.5.4") for p in row["provers"])
                    or any(p["success"] not in (0, 1) for p in row["provers"])
                    or any(p["success"] for p in row["provers"]) != row["passed"]):
                raise ValueError("unexecuted or inconsistent string-lemma proof")
            values[row["goal"].removeprefix("bytes_p20_string_witness_")] = (
                "VALID" if row["passed"] else "NOT_PROVED")
        negative = {"ensures"} if kind == "negative" else set()
        require_results(values, {"ensures", "assigns"} - negative, negative)
        outcomes[kind] = {"source_sha256":model.digest(source), "goals":values}
        print(f"string-lemma/{kind}: {values}; source_sha256={model.digest(source)}", flush=True)
    return outcomes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--why3", default="why3")
    ap.add_argument("--alt-ergo", default="alt-ergo")
    ap.add_argument("--config", type=Path)
    ap.add_argument("--theories-only", action="store_true",
                    help="local export diagnostics only; does not grant CI model acceptance")
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    args.model = args.model.resolve()
    receipt = model.check(args.model)
    why3 = run([args.why3, "--version"], args.output / "why3-version.log")
    alt = run([args.alt_ergo, "--version"], args.output / "alt-ergo-version.log")
    if why3.returncode or why3.stdout.strip() != "Why3 platform, version 1.8.2":
        raise ValueError("wrong Why3 version")
    if alt.returncode or alt.stdout.strip() != "v2.5.4":
        raise ValueError("wrong Alt-Ergo version")
    source = HERE / "phase20_bytes_model_canary.mlw"
    corrected = args.model / "share"
    outcomes = {}
    for name, share in (("original", model.INSTALLED), ("corrected", corrected)):
        expected = model.spec()["files"]["share/why3/frama_c_wp/membytes_le.mlw"][name]
        if model.digest(share / "why3/frama_c_wp/membytes_le.mlw") != expected:
            raise ValueError("canary model identity mismatch")
        values = solve(args, export(args, args.output / name, share, source))
        require_results(values, CONTROLS | NEGATIVES if name == "original" else CONTROLS,
                        set() if name == "original" else NEGATIVES)
        outcomes[name] = values
        for goal, value in sorted(values.items()):
            print(f"{name}/{goal}: {value}", flush=True)
    values = solve(args, export(args, args.output / "copy-regressions", corrected,
                               HERE / "phase20_model_copy_regressions.mlw",
                               ("-a", "compute_in_goal", "-a", "split_vc")))
    require_results(values, EXTRAS)
    outcomes["copy_regressions"] = values
    print("PASS: 7 copy/char-view/refutation regressions", flush=True)
    lemmas = {}
    for endian in ("le", "be"):
        for family in ("uint", "sint", "init"):
            for bits in (8, 16, 32, 64):
                name = f"read_{family}{bits}_copy_sep"
                files = export(args, args.output / "lemmas" / endian / name, corrected,
                               corrected / f"why3/frama_c_wp/membytes_{endian}.mlw",
                               ("-T", "MemBytes", "-G", name, "-a", "split_vc"))
                if len(files) != 2:
                    raise ValueError("changed library lemma subgoal inventory")
                values = solve(args, files)
                require_results(values, {name, name + "1"})
                lemmas[endian + "/" + name] = values
    outcomes["library_lemmas"] = lemmas
    print("PASS: 48/48 affected library subgoals across both byte orders", flush=True)
    if not args.theories_only:
        outcomes["readonly"] = readonly(args)
        print("PASS: readonly globals/literals and mutable global control; false writable-literal mutant rejected")
        outcomes["string_lemma"] = string_lemma(args)
        print("PASS: exact ghost string-witness lemma; missing-NUL-premise mutant rejected")
    report = {"format":"tombstone.phase20.corrected-model-regressions", "version":1,
              "build":receipt, "outcomes":outcomes,
              "status":"LOCAL_THEORY_DIAGNOSTICS_ONLY" if args.theories_only else "CANARY_PASSED_NOT_A_SOUNDNESS_PROOF"}
    (args.output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PASS: original contradiction reproduced; corrected model rejects it (not a general soundness proof)")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.TimeoutExpired) as error:
        raise SystemExit("FAIL: Phase 20 model canary: " + str(error)) from error
