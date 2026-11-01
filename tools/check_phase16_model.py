#!/usr/bin/env python3
"""Offline Phase 16 trust/target gate. Evidence is bounded, never a proof of hardware."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "machine/phase16/trust-boundaries-v1.json"
BASE = "c8ea4efc98f25a68b42ed051bcded0358ceb1e0a"
EXPECTED_SOURCES = {
    "src/core/deletion.c",
    "src/crypto/fingerprint.c",
    "src/crypto/fingerprint_hacl.c",
    "src/encoding/receipt.c",
    "include/tombstone/fingerprint.h",
    "include/tombstone/deletion.h",
    "include/tombstone/receipt.h",
    "machine/examples/explicit-delete-v1.json",
    "machine/examples/observed-transition-v1.json",
    "machine/examples/unchanged-v1.json",
}
CLASSES = {
    "A01": "conditional-proof", "A02": "conditional-proof",
    "A03": "tested", "A04": "tested", "A05": "tested",
    "A06": "tested", "A07": "tested",
    "A08": "trusted-assumption", "A09": "requires-external-evidence",
}
REQUIRED_KEYS = {
    "format", "version", "source_baseline_commit", "published_release",
    "source_git_blobs", "supported_targets", "boundaries", "chain_head_anchor",
    "physical_event_classes", "prohibited_claims", "excluded_evidence",
}
PROHIBITED = {
    "universally verified hardware", "independently authenticated deletion",
    "secure storage erasure", "proof of authorship",
    "trusted chronology without external witness",
    "verified machine code from repeat-build hashes",
}
PROBE_KEYS = {
    "format": "tombstone.phase16.target-observation",
    "char_bit": "8", "pointer_bits": "64", "size_t_bits": "64",
    "uint32_bits": "32", "uint64_bits": "64", "endianness": "little",
    "status_enum_bytes": "4", "evidence_enum_bytes": "4",
    "fingerprint_abi": "1", "evidence_abi": "1", "receipt_abi": "1",
}


def unique_keys(pairs: list[tuple[str, object]]) -> dict:
    out = {}
    for key, val in pairs:
        if key in out:
            raise ValueError("duplicate JSON key")
        out[key] = val
    return out


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def verify_manifest(record: dict, root: Path) -> None:
    assert isinstance(record, dict) and set(record) == REQUIRED_KEYS
    assert record["format"] == "tombstone.phase16.trust-boundaries"
    assert type(record["version"]) is int and record["version"] == 1
    assert record["source_baseline_commit"] == BASE
    assert record["published_release"] == {
        "tag": "v0.1.0", "scope": "immutable-original-source-only",
    }
    refs = record["source_git_blobs"]
    assert isinstance(refs, dict) and set(refs) == EXPECTED_SOURCES
    for name, sha in refs.items():
        assert re.fullmatch(r"[0-9a-f]{40}", sha)
        source = root / name
        assert source.is_file() and not source.is_symlink()
        assert git_blob(source.read_bytes()) == sha, f"source identity drift: {name}"

    target = record["supported_targets"]
    assert target == {
        "os": "linux", "architectures": ["x86_64", "aarch64"],
        "endianness": "little", "char_bit": 8, "pointer_bits": 64,
        "size_t_bits": 64, "compilers": ["gcc", "clang"],
        "hash_backends": ["openssl", "hacl"],
        "runtime_requirement": "valid-memory-no-undefined-behaviour",
    }
    boundaries = record["boundaries"]
    assert isinstance(boundaries, list) and len(boundaries) == len(CLASSES)
    assert [item.get("id") for item in boundaries] == list(CLASSES)
    for entry in boundaries:
        assert set(entry) == {"id", "classification", "scope", "run_url"}
        assert entry["classification"] == CLASSES[entry["id"]]
        assert isinstance(entry["scope"], str) and len(entry["scope"]) >= 35
        if entry["id"] in ("A08", "A09"):
            assert entry["run_url"] is None, "external premises cannot be CI proved"
        else:
            url = entry["run_url"]
            assert isinstance(url, str)
            assert re.fullmatch(
                r"https://github\.com/QSOLKCB/TOMBSTONE/actions/runs/[0-9]+", url
            )
    a = record["chain_head_anchor"]
    assert set(a) == {
        "format", "provided_by", "used_by", "proves", "does_not_prove"
    }
    assert "64 lowercase sha256 hex" in a["format"]
    assert "externally retained" in a["provided_by"]
    assert "C99 verify_chain" in a["used_by"]
    assert "conditional" in a["proves"]
    assert set(a["does_not_prove"]) == {
        "independent custody", "signer identity", "author",
        "chronology", "file deletion", "storage erasure",
    }
    physical = record["physical_event_classes"]
    assert isinstance(physical, list)
    assert [p.get("kind") for p in physical] == [
        "verified-splice-relation", "observed-filesystem-event", "storage-erasure"
    ]
    for item in physical:
        assert set(item) == {"kind", "evidence", "historical_claim_allowed"}
        assert type(item["historical_claim_allowed"]) is bool
        assert item["historical_claim_allowed"] is False
        assert isinstance(item["evidence"], str) and len(item["evidence"]) >= 35
    assert set(record["prohibited_claims"]) == PROHIBITED
    exclusions = record["excluded_evidence"]
    assert isinstance(exclusions, list) and len(exclusions) >= 3
    assert all(isinstance(x, str) and len(x) > 35 for x in exclusions)


def read_probe(path: Path) -> dict[str, str]:
    raw = path.read_bytes()
    assert len(raw) < 2048 and raw.endswith(b"\n")
    text = raw.decode("ascii")
    values: dict[str, str] = {}
    for line in text.splitlines():
        assert line.count("=") == 1
        key, value = line.split("=")
        assert key in PROBE_KEYS and key not in values
        values[key] = value
    assert values == PROBE_KEYS, "unsupported/modified target ABI observation"
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MODEL)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--probe", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        model = load_manifest(args.manifest)
        verify_manifest(model, args.repo_root)
        observation = None
        if args.probe is not None:
            assert platform.system() == "Linux"
            assert platform.machine() in model["supported_targets"]["architectures"]
            observation = read_probe(args.probe)
        if args.output is not None:
            assert observation is not None, "a target receipt requires an executed C probe"
            value = {
                "format": "tombstone.phase16.executed-target-receipt", "version": 1,
                "source_baseline_commit": BASE,
                "github_sha": os.environ.get("GITHUB_SHA"),
                "github_run_id": os.environ.get("GITHUB_RUN_ID"),
                "observed_architecture": platform.machine(),
                "kernel": platform.system(),
                "c_observation": observation,
                "observation_git_blobs": model["source_git_blobs"],
                "classification": "tested-on-this-target-not-a-hardware-proof",
            }
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    except (AssertionError, ValueError, UnicodeError, OSError, TypeError, KeyError) as e:
        raise SystemExit("FAIL: Phase 16 trust/target evidence gate: " + str(e)) from e
    print("PASS: pinned source, claim categories, custody limitations and physical-event bounds")
    if args.probe:
        print("PASS: executed C99 target observation matches declared Linux/64-bit/little-endian model")
    print("LIMIT: model tests cannot prove firmware, CPU, memory, signed history or storage erasure")


if __name__ == "__main__":
    main()
