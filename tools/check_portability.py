#!/usr/bin/env python3
"""Independent stdlib-Python cross-compiler receipt replay.

The checked code is the real Rust CLI -> C99 engine compiled independently
using GCC and Clang. Python is a test oracle only, not a shipped receipt API.
It uses the restricted receipt-v1 JSON profile (fixed ASCII strings, JSON-safe
integers). No arbitrary Unicode JCS support is claimed or required.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = b"TOMBSTONE-RECEIPT-V1\n"
FIXTURES = (
    "explicit-delete-v1.json",
    "observed-transition-v1.json",
    "unchanged-v1.json",
)
MAX_SAFE = (1 << 53) - 1


def canonical(value: dict) -> bytes:
    # RFC 8785 equivalent for the project's intentionally restricted schema.
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False,
        sort_keys=True, separators=(",", ":"),
    ).encode("ascii")


def independent_digest(receipt: dict) -> str:
    body = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    return hashlib.sha256(DOMAIN + canonical(body)).hexdigest()


def call(executable: str, *args: str, stdin: bytes | None = None,
         expected: int = 0) -> bytes:
    result = subprocess.run(
        [executable, *args], input=stdin, capture_output=True,
        check=False, timeout=20,
    )
    if result.returncode != expected:
        raise AssertionError(
            "unexpected TOMBSTONE CLI exit for operation "
            + str(args[0] if args else "(none)")
            + " (exit " + str(result.returncode) + ")"
        )
    if expected:
        assert not result.stdout, "CLI emitted success JSON on failure"
        assert result.stderr.startswith(b"tombstone:"), "CLI error not sanitized"
    else:
        assert not result.stderr, "CLI emitted unexpected stderr"
        assert result.stdout.endswith(b"\n")
    return result.stdout


def check(executable: str, temp: Path) -> list[bytes]:
    golden = [json.loads((ROOT / "machine" / "examples" / name).read_bytes())
              for name in FIXTURES]
    for receipt in golden:
        assert independent_digest(receipt) == receipt["receipt_hash"]

    before = str(ROOT / "tests/fixtures/before.txt")
    after = str(ROOT / "tests/fixtures/after.txt")
    removed = str(ROOT / "tests/fixtures/deleted.txt")
    output = []
    commands = [
        ("delete", before, removed, after, "4"),
        ("observe", before, after, "--previous", golden[0]["receipt_hash"]),
        ("observe", after, after, "--previous", golden[1]["receipt_hash"]),
    ]
    for index, args in enumerate(commands):
        payload = call(executable, *args)
        receipt = json.loads(payload)
        assert receipt == golden[index], "C99 receipt diverges from golden"
        assert payload == canonical(golden[index]) + b"\n", "noncanonical JSON"
        assert independent_digest(receipt) == receipt["receipt_hash"]
        assert b"1 2 3 4 5" not in payload, "plaintext found in receipt"
        output.append(payload)
        (temp / ("receipt-" + str(index) + ".json")).write_bytes(payload)

    expected_sha = hashlib.sha256(b"\x00\xff\x80\x00\n").hexdigest()
    binary = call(executable, "hash", "-", stdin=b"\x00\xff\x80\x00\n")
    assert json.loads(binary) == {"sha256": expected_sha, "size": 5}

    ordered = [str(temp / ("receipt-" + str(i) + ".json")) for i in range(3)]
    full = call(
        executable, "verify-chain", *ordered, "--trusted-head",
        golden[2]["receipt_hash"],
    )
    assert json.loads(full) == {
        "chain_valid": True, "count": 3,
        "head": golden[2]["receipt_hash"], "trusted_head_checked": True,
    }
    call(executable, "verify", ordered[1])
    call(executable, "verify-chain", ordered[1], ordered[0], expected=3)
    call(executable, "verify-chain", *ordered, "--trusted-head", "0" * 64, expected=3)
    call(executable, "verify-chain", ordered[1], ordered[2], expected=3)

    tampered = bytearray(output[0])
    marker = b'"version":1'
    at = tampered.index(marker)
    tampered[at + len(marker) - 1] = ord("2")
    call(executable, "verify", "-", stdin=bytes(tampered), expected=3)

    duplicate = b'{"version":1,' + output[0][1:]
    call(executable, "verify", "-", stdin=duplicate, expected=3)
    return output + [binary, full]


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: check_portability.py <gcc-cli> <clang-cli>")
    gcc = os.path.abspath(sys.argv[1])
    clang = os.path.abspath(sys.argv[2])
    with tempfile.TemporaryDirectory(prefix="tombstone-interop-") as d:
        base = Path(d)
        (base / "gcc").mkdir()
        (base / "clang").mkdir()
        a = check(gcc, base / "gcc")
        b = check(clang, base / "clang")
    assert a == b, "GCC and Clang C99 backends produced different CLI bytes"
    print("PASS: GCC/Clang native C99 via Rust CLI produced byte-identical receipts")
    print("PASS: independent Python SHA-256 domain-prefix and restricted JCS replay")
    print("PASS: anchored genesis chain, binary stdin and tamper/duplicate rejection")


if __name__ == "__main__":
    main()
