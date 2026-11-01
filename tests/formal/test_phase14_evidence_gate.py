#!/usr/bin/env python3
"""Regression for the Phase 14 stale-proof-pin incident (PR #20).

Test the actual fail-closed gate in an isolated copy, never by rewriting
repository proof sources or immutable receipt fixtures. A pin match asserts
source identity only: this is not a proof of the C99 algorithm or ABI.
"""
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "tools/check_phase14_evidence.py"
EXPECTED = {
    "src/encoding/receipt.c",
    "formal/framac/receipt_v14.c",
    "formal/cbmc/receipt_v14_harness.c",
    "machine/examples/explicit-delete-v1.json",
    "machine/examples/observed-transition-v1.json",
    "machine/examples/unchanged-v1.json",
}
CBMC_SOURCE = "formal/cbmc/receipt_v14_harness.c"
# Historical SHA from the stale reviewer finding. Never use it as live evidence.
STALE_CBMC_BLOB = "0c2601460e3e3bd5b75f0ebd89105435d20bc7b7"


def main() -> None:
    gate = runpy.run_path(str(CHECKER))
    pins = gate["BLOBS"]
    assert set(pins) == EXPECTED, "phase14 gate has lost a protected source/fixture"
    assert pins[CBMC_SOURCE] != STALE_CBMC_BLOB, "reviewed stale pin is live"
    assert all(len(value) == 40 for value in pins.values())

    # First require the checked-in sources to match their independently
    # computed Git blob hashes. The temporary tests below never modify them.
    for name, expected in pins.items():
        path = ROOT / name
        assert path.is_file() and not path.is_symlink(), f"missing proof input: {name}"
        assert gate["hash_blob"](path.read_bytes()) == expected, (
            f"checked-in pin is stale before testing: {name}"
        )

    with tempfile.TemporaryDirectory(prefix="tombstone-phase14-gate-") as tmp:
        sandbox = Path(tmp)
        isolated = sandbox / "tools/check_phase14_evidence.py"
        isolated.parent.mkdir(parents=True)
        shutil.copyfile(CHECKER, isolated)
        for name in sorted(pins):
            dest = sandbox / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)

        def run_gate(case: str, *, valid: bool, offending: str = "") -> None:
            result = subprocess.run(
                [sys.executable, str(isolated)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                check=False,
                cwd=sandbox,
            )
            output = result.stdout + result.stderr
            if valid:
                assert result.returncode == 0 and "PASS:" in output, (
                    f"{case}: valid inputs rejected: {output}"
                )
            else:
                assert result.returncode != 0 and "FAIL:" in output, (
                    f"{case}: evidence gate silently accepted invalid input: {output}"
                )
                assert offending in output, (
                    f"{case}: wrong failure reason: {output}"
                )

        run_gate("current pinned sources", valid=True)

        # Exact historical regression: the checker points at the previously
        # reviewed harness blob, despite the committed harness being different.
        original = isolated.read_text(encoding="utf-8")
        old = f'"{CBMC_SOURCE}": "{pins[CBMC_SOURCE]}"'
        bad = f'"{CBMC_SOURCE}": "{STALE_CBMC_BLOB}"'
        assert original.count(old) == 1
        isolated.write_text(original.replace(old, bad), encoding="utf-8")
        run_gate("stale reviewed CBMC SHA", valid=False, offending=CBMC_SOURCE)
        isolated.write_text(original, encoding="utf-8")
        run_gate("restored correct SHA", valid=True)

        # Each protected C source, formal overlay and immutable v1 fixture
        # must independently fail if its content changes without new proof.
        for name in sorted(pins):
            path = sandbox / name
            contents = path.read_bytes()
            assert contents
            try:
                path.write_bytes(contents + b"\nPHASE14_PROOF_INPUT_TAMPER\n")
                run_gate(f"modified {name}", valid=False, offending=name)
            finally:
                path.write_bytes(contents)

        path = sandbox / CBMC_SOURCE
        contents = path.read_bytes()
        path.unlink()
        run_gate("missing proof input", valid=False, offending=CBMC_SOURCE)

        # A symlink could redirect a purportedly pinned source to another file;
        # the gate must reject it even if the target has identical bytes.
        replacement = sandbox / "symlink-target.txt"
        replacement.write_bytes(contents)
        path.symlink_to(replacement)
        run_gate("symlinked proof input", valid=False, offending=CBMC_SOURCE)
        path.unlink()
        path.write_bytes(contents)
        run_gate("all original sources restored", valid=True)

    print("PASS: Phase 14 stale-pin incident, six source/fixture drifts, missing and symlinked proof inputs rejected")
    print("PASS: current committed source and corrected pin accepted")
    print("LIMIT: proof-input identity is not a proof of the hash provider, parser or compiled binary")


if __name__ == "__main__":
    main()
