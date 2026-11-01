#!/usr/bin/env python3
"""Offline fail-closed Phase 14 source/overlay/frozen-fixture identity gate.

No proof is created by comparing Git blobs. This pins which exact production
source and proof overlays a CI result may later describe. All frozen v1 JSON
examples must remain untouched.
"""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
BLOBS = {
    "src/encoding/receipt.c": "6fe3e8014e9c38ea42c43b9133f026967a4158e3",
    "formal/framac/receipt_v14.c": "d86fcf3dd1262c3061317fba715f12cfe864d87d",
    "formal/cbmc/receipt_v14_harness.c": "d06a231aea7c844de2185755faab84d63acb876c",
    "machine/examples/explicit-delete-v1.json": "3f3e1ba5f273bd266bcd764f10cd4e669f0dfc2d",
    "machine/examples/observed-transition-v1.json": "79dc897ad9192ed9eda8912213130c6556b72017",
    "machine/examples/unchanged-v1.json": "b712f23459b77ba7bb7fc9551df8af82ddc1ef33",
}


def hash_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def main() -> None:
    for name, expected in BLOBS.items():
        path = ROOT / name
        if not path.is_file() or path.is_symlink():
            raise SystemExit("FAIL: missing/nonregular Phase 14 proof source: " + name)
        actual = hash_blob(path.read_bytes())
        if actual != expected:
            raise SystemExit("FAIL: Phase 14 proof evidence stale: " + name +
                             " expected " + expected + " got " + actual)
    print("PASS: exact C99 receipt source, two formal overlays and 3 frozen v1 fixtures pinned")
    print("LIMIT: source identity alone is not runtime evidence or a formal proof")


if __name__ == "__main__":
    main()
