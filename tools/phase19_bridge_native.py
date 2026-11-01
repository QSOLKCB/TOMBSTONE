#!/usr/bin/env python3
"""Concrete counterexamples for the same semantic mutations used by WP.

Runs the preserved 13-case harness against real OpenSSL on positive paths.
Only disposable copies of receipt.c are mutated; build failures cannot pass.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile

import phase19_bridge_overlay as overlay
from phase19_negative_controls import ROOT, WRAPS

ASSERTIONS = {
    "missing-cleanup": "live == NULL",
    "caller-corruption": "memcmp(&saved, r, sizeof(saved)) == 0",
    "double-cleanup": "ctx == live && live != NULL",
}


def run(cc):
    with tempfile.TemporaryDirectory(prefix="p1903-native-") as directory:
        tmp = Path(directory)
        (tmp / "tests/formal").mkdir(parents=True)
        (tmp / "src/encoding").mkdir(parents=True)
        harness = tmp / "tests/formal/test_phase19_faults.c"
        original_harness = (ROOT / "tests/formal/test_phase19_faults.c").read_text()
        for name in ["positive", *ASSERTIONS]:
            source = overlay.render() if name == "positive" else overlay.mutant(name)
            native_source = overlay.strip(source)
            test = original_harness
            if name == "caller-corruption":
                # Parse the frozen setup fixture before enabling corruption.
                # Otherwise the fixture loader fails before the caller-frame assertion.
                test = test.replace('#include "../../src/encoding/receipt.c"',
                                    'static int p1903_fault_active;\n#include "../../src/encoding/receipt.c"')
                test = test.replace('    check_case(&r, NONE,',
                                    '    p1903_fault_active = 1;\n    check_case(&r, NONE,', 1)
                native_source = native_source.replace('    ((tb_receipt_v1 *)r)->has_previous ^= 1;',
                    '    if (p1903_fault_active) ((tb_receipt_v1 *)r)->has_previous ^= 1;', 1)
            harness.write_text(test)
            (tmp / "src/encoding/receipt.c").write_text(native_source)
            binary = tmp / name
            command = [cc, "-std=c99", "-O2", "-Wall", "-Wextra", "-Wpedantic", "-Werror",
                       "-I" + str(ROOT / "include"), str(harness),
                       str(ROOT / "src/crypto/fingerprint.c"), "-lcrypto", "-o", str(binary)]
            command.extend("-Wl,--wrap=" + symbol for symbol in WRAPS)
            subprocess.run(command, cwd=ROOT, check=True)
            result = subprocess.run([str(binary)], cwd=ROOT, capture_output=True,
                                    text=True, timeout=10)
            if name == "positive":
                if result.returncode != 0 or "PASS: 13 actual calculate_hash" not in result.stdout:
                    raise ValueError("positive actual helper failed: " + result.stderr)
            elif result.returncode != 1 or ASSERTIONS[name] not in result.stderr:
                raise ValueError("missing designated runtime counterexample: " + name)
            print("PASS:", cc, name, "13-path baseline" if name == "positive" else ASSERTIONS[name])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cc", default="gcc")
    run(parser.parse_args().cc)
