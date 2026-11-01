#!/usr/bin/env python3
"""Pinned upstream source identity and license check. Not an end-to-end proof."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent.parent
dir_ = root / "vendor/hacl-star"
source = dir_ / "dist/gcc-compatible/Hacl_Hash_SHA2.c"
license = dir_ / "dist/LICENSE.txt"
notice = dir_ / "UPSTREAM.md"
assert source.is_file() and license.is_file() and notice.is_file()
assert "MIT License" in license.read_text()
assert "f557259007db9933442dde10aa995c1b00bd3446" in notice.read_text()
blob = subprocess.check_output(["git", "hash-object", str(source)], text=True).strip()
print("PINNED_HACL_SHA2_C_BLOB=" + blob)
print("PASS: upstream provenance, vendor SHA2 source and MIT license present")
print("LIMIT: source identity is not proof of the adapter, compiler or executable")
