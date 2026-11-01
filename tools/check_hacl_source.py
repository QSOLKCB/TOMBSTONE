#!/usr/bin/env python3
"""Fail closed if ANY pinned upstream generated source/header/license differs.

These are Git blob SHA-1 identifiers taken from the exact upstream tree.
They are source provenance, not cryptographic proof of the adapter or binary.
"""
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent.parent
dir_ = root / "vendor/hacl-star"
manifest = json.loads((dir_ / "SOURCES.json").read_text(encoding="utf-8"))
notice = (dir_ / "UPSTREAM.md").read_text(encoding="utf-8")
assert manifest["upstream"] == "hacl-star/hacl-star"
assert len(manifest["commit"]) == 40 and manifest["commit"] in notice
assert len(manifest["git_blobs_sha1"]) >= 15
license = dir_ / "dist/LICENSE.txt"
assert "MIT License" in license.read_text(encoding="utf-8")
for name, expected in sorted(manifest["git_blobs_sha1"].items()):
    path = dir_ / name
    assert path.is_file(), f"missing pinned upstream file: {name}"
    got = subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()
    if got != expected:
        raise SystemExit(f"FAIL: altered upstream source/header: {name}; expected {expected}, observed {got}")
print(f"PASS: {len(manifest['git_blobs_sha1'])} immutable upstream source/header/license blob IDs match")
print("LIMIT: upstream identity does not formally verify the TOMBSTONE adapter or compiled executable")
