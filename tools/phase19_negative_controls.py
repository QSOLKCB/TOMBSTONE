#!/usr/bin/env python3
"""Semantic mutants are disposable test inputs, never proof/source baselines."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
WRAPS = ["snprintf", "__snprintf_chk", "tb_sha256_new", "tb_sha256_update",
         "tb_sha256_final", "tb_sha256_free"]


def native(cc):
    source = (ROOT / "src/encoding/receipt.c").read_text(encoding="utf-8")
    start = source.index("static tb_status calculate_hash(")
    end = source.index("\ntb_status tb_receipt_create(", start)
    body = source[start:end]
    mutations = {
        "always-equal": (source.replace("return memcmp(a, b, 32u) == 0;",
                                        "return memcmp(a, b, 32u) == 0 || 1;", 1),
                         "test_phase19_native.c"),
        "missing-cleanup": (source[:start] + body.replace("tb_sha256_free(ctx);", "(void)ctx;", 1)
                            + source[end:], "test_phase19_faults.c"),
        "write-on-error": (source[:start] + body.replace("    return st;",
                            "    if (st != TB_OK) out[0] ^= 1u;\n    return st;", 1)
                            + source[end:], "test_phase19_faults.c"),
        "swallowed-error": (source[:start] + body.replace("    return st;", "    return TB_OK;", 1)
                            + source[end:], "test_phase19_faults.c"),
    }
    with tempfile.TemporaryDirectory(prefix="phase19-mutants-") as directory:
        tmp = Path(directory)
        (tmp / "tests/formal").mkdir(parents=True)
        (tmp / "src/encoding").mkdir(parents=True)
        for name, (mutant, test) in mutations.items():
            if mutant == source:
                raise ValueError("missing mutation site: " + name)
            (tmp / "src/encoding/receipt.c").write_text(mutant, encoding="utf-8")
            shutil.copyfile(ROOT / "tests/formal" / test, tmp / "tests/formal" / test)
            binary = tmp / name
            command = [cc, "-std=c99", "-O2", "-Wall", "-Wextra", "-Wpedantic", "-Werror",
                       "-I" + str(ROOT / "include"), str(tmp / "tests/formal" / test),
                       str(ROOT / "src/crypto/fingerprint.c"), "-lcrypto", "-o", str(binary)]
            if test == "test_phase19_faults.c":
                command.extend("-Wl,--wrap=" + symbol for symbol in WRAPS)
            subprocess.run(command, cwd=ROOT, check=True)
            result = subprocess.run([str(binary)], cwd=ROOT, capture_output=True, text=True, timeout=10)
            if result.returncode != 1 or not re.search(r"FAIL|expected status", result.stderr):
                raise ValueError("mutant was not rejected by a test assertion: " + name)
            print("PASS: native semantic control rejected " + name)


def equal32_mutant(output):
    import phase19_equal32_overlay as overlay
    source = overlay.render()
    marker = "return memcmp(a, b, 32u) == 0;"
    if source.count(marker) != 1:
        raise ValueError("missing exact equal32 mutation site")
    output.write_text(source.replace(marker, "return memcmp(a, b, 32u) == 0 || 1;", 1),
                      encoding="utf-8")


def validate_negative_wp(text):
    if not re.search(r"(?m)^32\.1 \(Germanium\)\s*$", text):
        raise ValueError("mutant did not execute pinned Frama-C")
    if re.findall(r"\[rte:annot\] annotating function (\w+)", text) != ["equal32"]:
        raise ValueError("mutant did not execute equal32 RTE")
    summary = re.findall(r"\[wp\] Proved goals:\s*(\d+)\s*/\s*(\d+)", text)
    if len(summary) != 1:
        raise ValueError("mutant lacks an unambiguous executed proof result")
    proved, total = map(int, summary[0])
    if not 0 < proved < total:
        raise ValueError("mutated equality must leave a real proof obligation unproved")
    if re.findall(r"\[wp\]\s+(\d+) goals? scheduled", text) != [str(total)]:
        raise ValueError("mutant goal inventory is missing or ambiguous")
    if re.search(r"\[.*(?:error|abort).*\]|unsupported|Missing RTE", text, re.I):
        raise ValueError("tool/parse/model error is not a semantic negative control")
    if not re.search(r"\[wp\] \[(?:Unknown|Timeout|Failed)\]\s+"
                     r"bytes_equal32_ensures(?:_\w+)?\b", text):
        raise ValueError("no failed equal32 postcondition in mutant log")
    return proved, total


def negative_wp(log):
    proved, total = validate_negative_wp(log.read_text(encoding="utf-8"))
    print(f"PASS: unchanged contracts reject always-true equal32 ({proved}/{total})")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("native").add_argument("--cc", default="gcc")
    sub.add_parser("equal32-mutant").add_argument("--output", type=Path, required=True)
    sub.add_parser("check-negative-wp").add_argument("log", type=Path)
    args = parser.parse_args()
    if args.action == "native":
        native(args.cc)
    elif args.action == "equal32-mutant":
        equal32_mutant(args.output)
    else:
        negative_wp(args.log)


if __name__ == "__main__":
    main()
