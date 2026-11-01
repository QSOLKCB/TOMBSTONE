#!/usr/bin/env python3
"""Phase 15 executable comparison receipt (evidence, not compiler validation).

Builds are executed in GitHub Actions in independent Cargo target dirs using
the exact same source, CC, backend and release profile. The receipts record
the resulting bytes and source/toolchain identities; they do NOT prove that
the binaries refine the C99 source or that the environment is trustworthy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    "Cargo.lock",
    "bindings/rust/src/lib.rs",
    "bindings/rust/build.rs",
    "apps/cli/src/main.rs",
    "tests/phase15/abi_layout.c",
    "include/tombstone/fingerprint.h",
    "include/tombstone/deletion.h",
    "include/tombstone/receipt.h",
    "src/crypto/fingerprint.c",
    "src/crypto/fingerprint_hacl.c",
    "src/core/deletion.c",
    "src/encoding/receipt.c",
]


def command(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True, timeout=15).strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while data := stream.read(1024 * 1024):
            digest.update(data)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--compiler", choices=["gcc", "clang"], required=True)
    parser.add_argument("--backend", choices=["openssl", "hacl"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not args.first.is_file() or not args.second.is_file():
        raise SystemExit("FAIL: both independently built executables must exist")
    first_hash, second_hash = sha256_file(args.first), sha256_file(args.second)
    if first_hash != second_hash or args.first.stat().st_size != args.second.stat().st_size:
        raise SystemExit("FAIL: independently compiled release binaries differ byte-for-byte")

    sources = {
        name: command("git", "hash-object", str(ROOT / name))
        for name in SOURCES
    }
    record = {
        "format": "tombstone.phase15.target-build-evidence",
        "version": 1,
        "classification": "executed-binary-identity-not-compiler-proof",
        "source_commit": command("git", "rev-parse", "HEAD"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "target_arch": platform.machine(),
        "platform": platform.system(),
        "byteorder": sys.byteorder,
        "pointer_bits": 8 * (8 if sys.maxsize > (1 << 32) else 4),
        "compiler": args.compiler,
        "compiler_version": command(args.compiler, "--version").splitlines()[0],
        "rustc_version": command("rustc", "--version"),
        "cargo_version": command("cargo", "--version"),
        "archive_tool": command("ar", "--version").splitlines()[0],
        "sha_backend": args.backend,
        "profile": "release",
        "binary_sha256": first_hash,
        "binary_bytes": args.first.stat().st_size,
        "independent_builds_equal": True,
        "source_git_blobs": sources,
        "excluded_claims": [
            "No verified Rust to C semantics or universal ABI proof",
            "No CompCert or target-specific source-to-machine proof",
            "No proof of native or Rust compiler, linker, system libraries or hardware",
            "No proof of OpenSSL/HACL cryptography or historic erasure",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: two independently built native release executables have identical SHA-256")
    print("PASS: source, target/compiler, backend and toolchain identities captured")
    print("LIMIT: matching binaries do not establish verified compilation or semantic refinement")


if __name__ == "__main__":
    main()
