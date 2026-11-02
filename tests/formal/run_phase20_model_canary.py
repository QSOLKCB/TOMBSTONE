#!/usr/bin/env python3
"""Fail closed if the pinned Bytes theory proves a concrete contradiction."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
MODEL_SHA256 = "16478d1b77f282539b642b174bbf8225a5d30fe0442e5e1cd46ada8e1f05c61a"
CONTROLS = {"destination_before", "source_before", "neighbour_is_separate", "library_frame_value"}
NEGATIVES = {"definition_value", "contradictory_values"}


def run(command, log):
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
    log.write_text(result.stdout)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--why3", default="why3")
    ap.add_argument("--alt-ergo", default="alt-ergo")
    ap.add_argument("--config", type=Path)
    ap.add_argument("--wp-share", type=Path,
                    default=Path("/home/opam/.opam/4.14/share/frama-c/share/wp/why3"))
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    tasks = args.output / "tasks"
    tasks.mkdir()  # Refuse stale exported tasks, including an earlier failed run.
    model = args.wp_share / "frama_c_wp/membytes_le.mlw"
    model_digest = hashlib.sha256(model.read_bytes()).hexdigest()
    if model_digest != MODEL_SHA256:
        raise ValueError("unreviewed Bytes theory identity")
    why3 = run([args.why3, "--version"], args.output / "why3-version.log")
    alt = run([args.alt_ergo, "--version"], args.output / "alt-ergo-version.log")
    if why3.returncode or why3.stdout.strip() != "Why3 platform, version 1.8.2":
        raise ValueError("wrong Why3 version")
    if alt.returncode or alt.stdout.strip() != "v2.5.4":
        raise ValueError("wrong Alt-Ergo version")
    source = HERE / "phase20_bytes_model_canary.mlw"
    command = [args.why3, "prove"]
    if args.config:
        command += ["--config", str(args.config)]
    command += ["-L", str(args.wp_share), "-P", "Alt-Ergo,2.5.4,", "-o", str(tasks), str(source)]
    export = run(command, args.output / "export.log")
    if export.returncode:
        raise ValueError("Why3 task export failed")
    exported = list(tasks.glob("*.psmt2"))
    files = {p.stem.rsplit("-", 1)[-1]: p for p in exported}
    if len(exported) != len(CONTROLS | NEGATIVES) or set(files) != CONTROLS | NEGATIVES:
        raise ValueError("missing, duplicate or unexpected canary goals")
    outcomes = {}
    for name, path in sorted(files.items()):
        result = run([args.alt_ergo, "--frontend", "dolmen", "--timelimit", "10", str(path)],
                     args.output / (name + ".log"))
        valid = len(re.findall(r"\bValid \(", result.stdout)) == 1 and re.findall(r"(?m)^unsat$", result.stdout) == ["unsat"]
        if result.returncode or re.search(r"\b(error|exception)\b", result.stdout, re.I):
            raise ValueError("canary solver failed: " + name)
        if not valid and not re.search(r"(?m)^(sat|unknown)$", result.stdout):
            raise ValueError("unrecognized solver result: " + name)
        outcomes[name] = "VALID" if valid else "NOT_PROVED"
    if any(outcomes[name] != "VALID" for name in CONTROLS):
        raise ValueError("positive canary control did not pass")
    inconsistent = any(outcomes[name] == "VALID" for name in NEGATIVES)
    report = {
        "format": "tombstone.phase20.bytes-model-canary", "version": 1,
        "model_sha256": model_digest, "probe_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "why3": "1.8.2", "alt_ergo": "2.5.4", "goals": outcomes,
        "status": "BLOCKED_MODEL_INCONSISTENCY" if inconsistent else "CANARY_PASSED_NOT_A_SOUNDNESS_PROOF",
    }
    (args.output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    for name, outcome in sorted(outcomes.items()):
        print(f"{name}: {outcome}")
    if inconsistent:
        raise ValueError("pinned Bytes theory proves contradictory byte values; Phase 20 proof acceptance blocked")
    print("PASS: positive controls executed; false byte-copy claims not proved (not a soundness proof)")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        raise SystemExit("FAIL: Phase 20 model canary: " + str(error)) from error
