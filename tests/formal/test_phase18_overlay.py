#!/usr/bin/env python3
"""Validate that Phase 18 proof never substitutes a toy chain or drifts source."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import hashlib
import tempfile

ROOT=Path(__file__).resolve().parents[2]
p=ROOT/"tools/phase18_wp_overlay.py"
spec=importlib.util.spec_from_file_location("phase18_overlay",p)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
original=mod.SOURCE.read_bytes()
assert mod.git_blob(original)==mod.EXPECTED_BLOB
source=original.decode("utf-8")
overlay=mod.render(source)
assert overlay.count("tb_status tb_receipt_verify_chain(")==1
assert overlay.count("static tb_status calculate_hash(")==1
assert overlay.count("static int equal32(")==1
assert len(mod.ANNOTATIONS)==4
for marker, annotation in mod.ANNOTATIONS.items():
    assert overlay.count(marker)==1
    assert overlay.count(annotation)==1
    assert annotation.startswith("/*@") and annotation.rstrip().endswith("*/")
stripped=overlay
for annotation in mod.ANNOTATIONS.values():
    stripped=stripped.replace(annotation,"",1)
assert stripped.encode("utf-8")==original
assert mod.git_blob(stripped.encode("utf-8"))==mod.EXPECTED_BLOB
for marker in mod.ANNOTATIONS:
    try: mod.render(source.replace(marker,marker+" #tampered"))
    except ValueError: pass
    else: raise AssertionError("nonunique or shifted production insertion passed: "+marker[:70])
try: mod.render(source.replace("tb_receipt_verify_chain", "fake_chain"))
except ValueError: pass
else: raise AssertionError("missing actual public verifier accepted")
assert "requires \\valid_read(receipts+(0 .. count-1));" in overlay
assert "requires 1 <= count <= SIZE_MAX / sizeof(tb_receipt_v1);" in overlay
assert "loop variant count - i;" in overlay
assert "loop assigns i, st, computed[0 .. 31];" in overlay
assert "assigns \\nothing;" in overlay
assert "ensures \\result == TB_OK && trusted_head != \\null" in overlay
with tempfile.TemporaryDirectory(prefix="tombstone-phase18-") as folder:
    outfile=Path(folder)/"acsl.c"
    outfile.write_text(overlay)
    assert outfile.read_bytes().replace(b"/*@", b"/*@", 1)==overlay.encode()
print("PASS: Phase 18 annotation-only proof translation unit strips to exact published C99 blob")
print("PASS: required SHA/equality assumptions, unbounded loop invariants and postconditions present")
