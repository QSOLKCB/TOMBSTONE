#!/usr/bin/env python3
"""Phase 16 fail-closed trust-model regressions, no live source mutation."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "tools/check_phase16_model.py"

spec = importlib.util.spec_from_file_location("phase16_check", CHECKER)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
model = module.load_manifest(module.MODEL)
module.verify_manifest(model, ROOT)


def rejected(record: dict, reason: str) -> None:
    try:
        module.verify_manifest(record, ROOT)
    except (AssertionError, ValueError, TypeError, KeyError):
        return
    raise AssertionError(f"invalid Phase 16 premise accepted: {reason}")


broken = copy.deepcopy(model)
broken["boundaries"][-1]["classification"] = "conditional-proof"
rejected(broken, "claim historical deletion was proved")
broken = copy.deepcopy(model)
broken["boundaries"][-2]["run_url"] = (
    "https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41321354704"
)
rejected(broken, "claim OS/hardware were verified in CI")
broken = copy.deepcopy(model)
broken["physical_event_classes"][2]["historical_claim_allowed"] = True
rejected(broken, "assert complete storage erasure")
broken = copy.deepcopy(model)
broken["chain_head_anchor"]["does_not_prove"].remove("independent custody")
rejected(broken, "silently upgrade an anchor into external custody")
broken = copy.deepcopy(model)
broken["supported_targets"]["architectures"].append("unknown-machine")
rejected(broken, "invent target architecture")
broken = copy.deepcopy(model)
broken["published_release"]["tag"] = "v0.2.0"
rejected(broken, "alter the immutable source release identity")
broken = copy.deepcopy(model)
broken["prohibited_claims"].remove("trusted chronology without external witness")
rejected(broken, "erase a prohibited time claim")
broken = copy.deepcopy(model)
broken["source_git_blobs"]["src/core/deletion.c"] = "0" * 40
rejected(broken, "change production C99 source pin without evidence")

with tempfile.TemporaryDirectory(prefix="tombstone-phase16-gate-") as temp:
    directory = Path(temp)
    duplicate_json = directory / "duplicate.json"
    raw = module.MODEL.read_text(encoding="utf-8")
    assert raw.startswith("{")
    duplicate_json.write_text(raw.replace('"version": 1,', '"version": 1, "version": 1,', 1))
    try:
        module.load_manifest(duplicate_json)
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate JSON keys accepted")

    # A second root allows actual source-byte tampering without changing the
    # repository checkout or the preserved frozen v1 receipt fixtures.
    for name in model["source_git_blobs"]:
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, path)
    module.verify_manifest(model, directory)
    target = directory / "machine/examples/unchanged-v1.json"
    target.write_bytes(target.read_bytes() + b"\n")
    try:
        module.verify_manifest(model, directory)
    except AssertionError:
        pass
    else:
        raise AssertionError("changed historical v1 receipt accepted")

    lines = "\n".join(f"{key}={value}" for key, value in module.PROBE_KEYS.items()) + "\n"
    probe = directory / "probe.txt"
    probe.write_text(lines, encoding="ascii")
    assert module.read_probe(probe) == module.PROBE_KEYS
    for kind, altered in [
        ("incorrect-endian", lines.replace("endianness=little", "endianness=big")),
        ("wrong-pointer-model", lines.replace("pointer_bits=64", "pointer_bits=32")),
        ("duplicate", lines + "char_bit=8\n"),
        ("alien-field", lines + "hardware_verified=true\n"),
        ("no-trailing-LF", lines.rstrip("\n")),
    ]:
        probe.write_text(altered, encoding="ascii")
        try:
            module.read_probe(probe)
        except (AssertionError, ValueError, UnicodeError):
            continue
        raise AssertionError("invalid C99 target observation accepted: " + kind)

    # Execute the actual CLI parser/gate once, not just imported helpers.
    result = subprocess.run(
        [sys.executable, str(CHECKER)], capture_output=True,
        text=True, check=False, timeout=10,
    )
    assert result.returncode == 0 and "PASS:" in result.stdout, result.stderr

print("PASS: Phase 16 rejects false historical/hardware/erasure assurances and source drift")
print("PASS: manifest duplicate keys and malformed target observations fail closed")
print("LIMIT: these are model and integrity tests, not hardware or historical proofs")
