#!/usr/bin/env python3
"""Reject any changed Phase 17 proof source, harness or frozen fixture."""
import importlib.util
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/check_phase17_evidence.py"
spec = importlib.util.spec_from_file_location("phase17_gate", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert len(module.BLOBS) == 6
assert set(module.BLOBS) == {
    "src/encoding/receipt.c", "formal/cbmc/chain_v17_harness.c",
    "tests/formal/test_chain_v17.c",
    "machine/examples/explicit-delete-v1.json",
    "machine/examples/observed-transition-v1.json",
    "machine/examples/unchanged-v1.json",
}
module.verify(ROOT)
with TemporaryDirectory(prefix="tombstone-phase17-evidence-") as tmp:
    base = Path(tmp)
    for name in module.BLOBS:
        f = base / name
        f.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, f)
    module.verify(base)
    for name in module.BLOBS:
        f = base / name
        original = f.read_bytes()
        f.write_bytes(original + b"\nmodified\n")
        try:
            module.verify(base)
        except ValueError as e:
            assert name in str(e)
        else:
            raise AssertionError("modified input passed: " + name)
        f.write_bytes(original)
    target = base / "formal/cbmc/chain_v17_harness.c"
    target.unlink()
    try:
        module.verify(base)
    except ValueError:
        pass
    else:
        raise AssertionError("missing CBMC source accepted")
    target.symlink_to(ROOT / "formal/cbmc/chain_v17_harness.c")
    try:
        module.verify(base)
    except ValueError:
        pass
    else:
        raise AssertionError("symlink CBMC input accepted")
print("PASS: six source/fixture drifts, deleted and symlinked proof inputs all fail closed")
