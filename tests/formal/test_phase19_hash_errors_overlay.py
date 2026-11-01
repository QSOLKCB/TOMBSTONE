#!/usr/bin/env python3
"""The stronger error-output claim must remain on the original C body."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import phase19_hash_errors_overlay as current

old = current.original
rendered = current.render()
assert "TB_ERR_LENGTH" in current.UPDATED
assert current.FAILURE in current.HASH_CONTRACT
assert current.FAILURE in current.MODEL
assert current.MODEL.count(current.FAILURE) == 1
stripped = rendered.replace(current.MODEL, "", 1)
stripped = stripped.replace(current.HASH_CONTRACT, "", 1)
stripped = stripped.replace(old.FORMAT, "", 1).replace(old.GOOD, "", 1)
for marker, annotation in old.m.ANNOTATIONS.items():
    if marker != old.HASH_MARKER:
        stripped = stripped.replace(annotation, "", 1)
assert stripped == old.m.SOURCE.read_text(encoding="utf-8")
assert "assigns out[0 .. 31], model_private_provider_state;" in current.HASH_CONTRACT
print("PASS: extended error contracts preserve actual source and disclose the private-state frame")
