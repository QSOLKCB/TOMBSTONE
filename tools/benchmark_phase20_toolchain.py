#!/usr/bin/env python3
"""Measure three cold/reuse pairs, including fresh canaries in every trial."""
import argparse
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import time

import phase20_toolchain_reuse as reuse


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def command(args, log):
    started = time.monotonic()
    with log.open("w") as stream:
        subprocess.run(args, stdout=stream, stderr=subprocess.STDOUT, check=True)
    return time.monotonic() - started


def semantic(value):
    # False controls may return unknown or time out. Neither is a proof.
    if isinstance(value, dict):
        return {k: semantic(v) for k, v in value.items()}
    return "NOT_PROVED" if value == "TIMEOUT_NOT_PROVED" else value


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    output = args.output.resolve()
    output.mkdir()
    source = reuse.ROOT
    _, state = reuse.identity()
    if not state["eligible"]:
        raise ValueError("benchmark requires an exactly eligible approved toolchain")
    context = {"format": "tombstone.phase20.toolchain-benchmark", "version": 1,
        "scope": "MODEL_PREPARATION_AND_FRESH_CANARIES_ONLY",
        "checkout_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "pr_head_sha": os.environ.get("PR_HEAD_SHA"), "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"), "image": reuse.IMAGE,
        "key": state["key"], "input_sha256": state["input_sha256"],
        "host": {"platform": platform.platform(), "cpu_count": os.cpu_count(),
                 "runner_image": os.environ.get("ImageOS"), "runner_version": os.environ.get("ImageVersion")},
        "required_median_reduction_fraction": 0.10, "proof_results_reused": False, "trials": []}
    write(output / "result.json", context)
    context["shared_image_pull_seconds"] = command(["docker", "pull", reuse.IMAGE], output / "image-pull.log")
    command(["docker", "image", "inspect", reuse.IMAGE], output / "image-inspect.json")
    cache = output / "transport/approved.zip"
    expected_outcomes = None
    # Alternate pair order; no warm-up samples are silently discarded.
    for number, modes in enumerate((("cold", "reuse"), ("reuse", "cold"), ("cold", "reuse")), 1):
        for mode in modes:
            trial = output / f"{number}-{mode}"
            trial.mkdir()
            trial.chmod(0o777)
            started = time.monotonic()
            report = reuse.acquire(trial / "model", cache, force_cold=mode == "cold", expected_key=state["key"])
            write(trial / "preparation.json", report)
            build_seconds = 0.0
            if mode == "reuse" and report["mode"] != "REUSED_VERIFIED_TOOLCHAIN":
                raise ValueError("candidate was not reused; benchmark cannot label fallback as a hit")
            if mode == "cold":
                build_seconds = command(["docker", "run", "--rm", "-v", f"{source}:/repo:ro",
                    "-v", f"{trial}:/out", reuse.IMAGE, "python3", "/repo/tools/phase20_model.py",
                    "build", "--output", "/out/model"], trial / "build.log")
            canary_seconds = command(["docker", "run", "--rm", "-v", f"{source}:/repo:ro",
                "-v", f"{trial}:/out", "-v", f"{trial / 'model'}:/model:ro", reuse.IMAGE,
                "python3", "/repo/tests/formal/run_phase20_model_canary.py", "--model", "/model",
                "--output", "/out/regressions"], trial / "canary.log")
            report = reuse.complete(report, trial / "model", trial / "regressions/result.json")
            elapsed = time.monotonic() - started
            write(trial / "preparation.json", report)
            outcomes = semantic(reuse.load((trial / "regressions/result.json").read_bytes())["outcomes"])
            if expected_outcomes is None:
                expected_outcomes = outcomes
            if outcomes != expected_outcomes:
                raise ValueError("cold and reuse canary inventories or semantic outcomes differ")
            row = {"trial": number, "requested_mode": mode, "preparation": report,
                   "build_seconds": build_seconds, "canary_seconds": canary_seconds,
                   "elapsed_seconds": elapsed, "outcome_sha256": reuse.sha(reuse.canonical(outcomes))}
            context["trials"].append(row)
            write(output / "result.json", context)
            print(f"{number}/{mode}: {elapsed:.3f}s; build={build_seconds:.3f}s; canary={canary_seconds:.3f}s", flush=True)
    medians = {mode: statistics.median(r["elapsed_seconds"] for r in context["trials"] if r["requested_mode"] == mode)
               for mode in ("cold", "reuse")}
    fraction = 1 - medians["reuse"] / medians["cold"]
    context.update(median_seconds=medians, median_reduction_fraction=fraction,
                   material_reduction_observed=fraction >= context["required_median_reduction_fraction"],
                   status="SIX_TRIALS_COMPLETE_WITH_FRESH_CANARIES")
    write(output / "result.json", context)
    print(json.dumps({k: context[k] for k in ("median_seconds", "median_reduction_fraction", "material_reduction_observed", "status")}), flush=True)
    if not context["material_reduction_observed"]:
        raise ValueError("predeclared 10% model-stage benefit not observed; do not promote reuse")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit("FAIL: Phase 20 toolchain benchmark: " + str(error)) from error
