#!/usr/bin/env python3
"""Bind CI-only changes without relabelling the preserved Phase 20 execution."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = "machine/formal/phase20-replay-binding-v1.json"
HISTORY = "machine/formal/phase20-evidence-v2.json"
HISTORY_SHA256 = "4b612b8d868a163ac16327f094d08788950a6fc089639ad3307b3f1ed31c5593"
REPLACED = {".github/workflows/phase20-receipt-prerequisites.yml", "tools/check_phase20_evidence.py"}
ADDED = {"tools/check_phase20_replay_binding.py", "tests/formal/test_phase20_replay_binding.py",
         "tools/phase20_toolchain_reuse.py", "tests/formal/test_phase20_toolchain_reuse.py",
         "machine/formal/phase20-toolchain-reuse-v1.json", "tools/benchmark_phase20_toolchain.py",
         ".github/workflows/phase20-toolchain-reuse-benchmark.yml"}


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate replay binding key")
        result[key] = value
    return result


def read(root, name):
    path = root / name
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError("missing or aliased replay dependency: " + name)
    return path.read_bytes()


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def validate(source_blobs, root=ROOT):
    original = read(root, HISTORY)
    if hashlib.sha256(original).hexdigest() != HISTORY_SHA256:
        raise ValueError("historical Phase 20 evidence changed")
    history = json.loads(original, object_pairs_hook=unique)["source_blobs"]
    # Keep all semantic evidence mutations visible to the original validator.
    # Only its dependency map is compared here, not the supplied whole record.
    if source_blobs != history:
        raise ValueError("stale proof dependency: historical source map changed")
    binding = json.loads(read(root, RECORD), object_pairs_hook=unique)
    if set(binding) != {"format", "version", "scope", "historical_sha256", "current_blobs"} or type(binding["version"]) is not int:
        raise ValueError("invalid replay binding fields")
    if (binding["format"], binding["version"], binding["scope"], binding["historical_sha256"]) != (
            "tombstone.phase20.replay-binding", 1, "CI_ORCHESTRATION_ONLY_NO_NEW_PROOF", HISTORY_SHA256):
        raise ValueError("invalid replay binding scope or history")
    current = binding["current_blobs"]
    if set(current) != REPLACED | ADDED:
        raise ValueError("missing or unexpected replay dependency")
    # This fixed allowlist cannot exempt C, contracts, models, provers, goals,
    # fixtures or proof checkers from their original source identities.
    expected = {p: h for p, h in history.items() if p not in REPLACED} | current
    for path, digest in expected.items():
        if git_blob(read(root, path)) != digest:
            raise ValueError("stale proof dependency: " + path)


if __name__ == "__main__":
    try:
        original = json.loads(read(ROOT, HISTORY), object_pairs_hook=unique)
        validate(original["source_blobs"])
        print("PASS: unchanged proof inputs; explicit CI replay binding; no new proof claimed")
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise SystemExit("FAIL: Phase 20 replay binding: " + str(error)) from error
