#!/usr/bin/env python3
"""Require Frama-C WP to prove every nonzero VC (no vacuous green CI)."""
import pathlib
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: check_wp_proofs.py <wp-log>")
content = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
matches = re.findall(r"Proved goals:\s*(\d+)\s*/\s*(\d+)", content)
if not matches:
    raise SystemExit("FAIL: missing Frama-C WP goal summary (no proof evidence)")
proved, total = (int(x) for x in matches[-1])
if total == 0 or proved != total:
    raise SystemExit(f"FAIL: WP obligations incomplete: {proved}/{total}; see full log")
print(f"PASS: Frama-C WP discharged all {total} non-vacuous goals")
