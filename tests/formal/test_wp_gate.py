#!/usr/bin/env python3
"""Negative controls ensure incomplete/vacuous WP logs fail the CI parser."""
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys

CHECKER = Path(__file__).resolve().parents[2] / "tools/check_wp_proofs.py"
CASES = [
    ("missing", "[wp] Running WP plugin...", False),
    ("vacuous", "[wp] Proved goals: 0 / 0", False),
    ("partial", "[wp] Proved goals: 12 / 13", False),
    ("correct", "[wp] Proved goals: 35 / 35", True),
]
with TemporaryDirectory(prefix="tombstone-wp-negative-") as folder:
    for name, output, expected in CASES:
        filename = Path(folder) / (name + ".log")
        filename.write_text(output + "\n", encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(CHECKER), str(filename)],
            capture_output=True, check=False, timeout=5,
        )
        passed = completed.returncode == 0
        if passed != expected:
            raise SystemExit(f"FAIL: WP log gate accepted wrong verdict for {name}")
print("PASS: WP gate rejects missing, zero-goal and incomplete proof evidence")
