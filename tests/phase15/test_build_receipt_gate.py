#!/usr/bin/env python3
"""Phase 15 proof receipt gate negative controls (no source mutation)."""
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "tools/phase15_build_receipt.py"

with tempfile.TemporaryDirectory(prefix="tombstone-phase15-negative-") as tmp:
    root = Path(tmp)
    a, b, output = root / "a", root / "b", root / "evidence.json"
    a.write_bytes(b"native-build-A")
    b.write_bytes(b"native-build-B")
    result = subprocess.run(
        [sys.executable, str(CHECKER), "--first", str(a), "--second", str(b),
         "--compiler", "gcc", "--backend", "openssl", "--output", str(output)],
        capture_output=True, text=True, timeout=15, check=False,
    )
    assert result.returncode != 0
    assert "FAIL: independently compiled release binaries differ byte-for-byte" in (
        result.stderr + result.stdout
    )
    assert not output.exists(), "mismatched binaries must never receive a pass receipt"

    b.unlink()
    missing = subprocess.run(
        [sys.executable, str(CHECKER), "--first", str(a), "--second", str(b),
         "--compiler", "gcc", "--backend", "openssl", "--output", str(output)],
        capture_output=True, text=True, timeout=15, check=False,
    )
    assert missing.returncode != 0
    assert "FAIL: both independently built executables must exist" in (
        missing.stderr + missing.stdout
    )
    assert not output.exists()

print("PASS: unequal or missing binaries fail closed without manufacturing evidence")
