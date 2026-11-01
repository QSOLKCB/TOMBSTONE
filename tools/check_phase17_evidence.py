#!/usr/bin/env python3
"""Phase 17 offline exact-source identity gate (not a proof of properties)."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
BLOBS = {
    "src/encoding/receipt.c": "6fe3e8014e9c38ea42c43b9133f026967a4158e3",
    "formal/cbmc/chain_v17_harness.c": "01db6e5e89b4c2d837368dd711fe8fe34ff124e6",
    "tests/formal/test_chain_v17.c": "d798ab41664bf66b477ffeecadd0e5ed885f1d53",
    "machine/examples/explicit-delete-v1.json": "3f3e1ba5f273bd266bcd764f10cd4e669f0dfc2d",
    "machine/examples/observed-transition-v1.json": "79dc897ad9192ed9eda8912213130c6556b72017",
    "machine/examples/unchanged-v1.json": "b712f23459b77ba7bb7fc9551df8af82ddc1ef33",
}

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def verify(root: Path = ROOT) -> None:
    for name, expected in BLOBS.items():
        f = root / name
        if not f.is_file() or f.is_symlink():
            raise ValueError("missing, symlinked or nonregular proof input: " + name)
        if git_blob(f.read_bytes()) != expected:
            raise ValueError("stale proof evidence input: " + name)

def main() -> None:
    try:
        verify()
    except ValueError as error:
        raise SystemExit("FAIL: " + str(error)) from error
    print("PASS: exact authoritative C99 chain source, direct CBMC overlay, runtime replay and frozen v1 receipts")
    print("LIMIT: matching blobs neither prove chain semantics nor authenticate real-world events")

if __name__ == "__main__":
    main()
