#!/usr/bin/env python3
"""Fail-closed, offline Git blob identity check of pinned HACL* source files.

The expected hashes were read from the upstream Git tree at commit
f557259007db9933442dde10aa995c1b00bd3446. This verifies source
identity, not upstream proof reproduction, C/Rust adapter correctness,
the compiled binary or hardware.
"""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "vendor" / "hacl-star"
REVISION = "f557259007db9933442dde10aa995c1b00bd3446"
BLOBS = {
    "dist/LICENSE.txt": "ffdc21a61431e8c4de5bdd83f63fc91bbf3331c3",
    "dist/gcc-compatible/Hacl_Hash_SHA2.c": "ec97803fdc1296daf3aa7b5cb54cd3358c6fe236",
    "dist/gcc-compatible/Hacl_Hash_SHA2.h": "51ca9febdfdb3f7041eb9bf725e29f1ba3054b87",
    "dist/gcc-compatible/Hacl_Krmllib.h": "b8b930565be2c8776f9053c1ca2d2a3a1cfdea91",
    "dist/gcc-compatible/Hacl_Streaming_Types.h": "cce25eb794675020b22d852444b4cb20265dff88",
    "dist/gcc-compatible/internal/Hacl_Hash_SHA2.h": "e6750207980aef902e1a56aba02d21b81161776f",
    "dist/gcc-compatible/internal/Hacl_Krmllib.h": "c89f30840f6bca78d2a23e0f6ade9fc672725ff9",
    "dist/gcc-compatible/internal/Hacl_Streaming_Types.h": "d6c4fc0d6255f73972af324be691360813341abc",
    "dist/karamel/include/krml/internal/compat.h": "f206520fc0f4a4a007860c1b8e80a6d1892ee2c6",
    "dist/karamel/include/krml/internal/target.h": "5cdd641c228d9d403a7074a7ac3609d52fdc6f41",
    "dist/karamel/include/krml/internal/types.h": "21dadeb0afa8c9994421bdbab6fc75a1224f8c10",
    "dist/karamel/include/krml/lowstar_endianness.h": "72b932221264fb8294cd93bdbfeeca6ae197e306",
    "dist/karamel/krmllib/dist/minimal/FStar_UInt128.h": "a0b2cf1ee2b9be7dbca85baf0b77d854c9a0014b",
    "dist/karamel/krmllib/dist/minimal/FStar_UInt_8_16_32_64.h": "bdb8adeb8a2a8663b2185879e7718eb578ebba66",
    "dist/karamel/krmllib/dist/minimal/LowStar_Endianness.h": "0d47e368b3583a1afd49704419cb6cea2fd38c60",
    "dist/karamel/krmllib/dist/minimal/fstar_uint128_gcc64.h": "10a4dc1aae484914dddbd262ff86622972d6edc5"
}


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def main() -> None:
    notice = (VENDOR / "UPSTREAM.md").read_text(encoding="utf-8")
    if REVISION not in notice:
        raise SystemExit("FAIL: pinned upstream revision missing from UPSTREAM.md")

    actual_files = {
        str(path.relative_to(VENDOR))
        for path in (VENDOR / "dist").rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if actual_files != set(BLOBS):
        raise SystemExit(
            "FAIL: vendor file set drift: missing="
            + repr(sorted(set(BLOBS) - actual_files))
            + " extra=" + repr(sorted(actual_files - set(BLOBS)))
        )
    for relative, expected in sorted(BLOBS.items()):
        path = VENDOR / relative
        if not path.is_file() or path.is_symlink():
            raise SystemExit("FAIL: missing, nonregular or symlinked vendor file " + relative)
        observed = git_blob_sha(path.read_bytes())
        if observed != expected:
            raise SystemExit(
                "FAIL: upstream Git blob mismatch in " + relative
                + "; expected=" + expected + " observed=" + observed
            )
    if b"MIT License" not in (VENDOR / "dist/LICENSE.txt").read_bytes():
        raise SystemExit("FAIL: expected MIT distribution license missing")
    print(f"PASS: {len(BLOBS)} pinned HACL*/KaRaMeL Git blobs match upstream commit {REVISION}")
    print("LIMIT: source identity is not a proof of this adapter, compiler or hardware")


if __name__ == "__main__":
    main()
