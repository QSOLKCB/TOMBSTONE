#!/usr/bin/env python3
"""Check public TOMBSTONE documentation examples, NOT general receipt verification.

Only supports the documented restricted v1 JSON value subset; it is not an
RFC 8785/JCS implementation or a full JSON Schema validator.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ORDER = (
    "explicit-delete-v1.json",
    "observed-transition-v1.json",
    "unchanged-v1.json",
)
HASH = re.compile(r"[0-9a-f]{64}\Z")
MAX_SAFE_INTEGER = 9007199254740991
DOMAIN = b"TOMBSTONE-RECEIPT-V1\n"
RECEIPT_FIELDS = {
    "format", "version", "kind", "before", "after", "deleted",
    "previous_receipt_hash", "receipt_hash",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"),
                      object_pairs_hook=reject_duplicate_keys,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError("invalid JSON constant: " + value)))


def safe_int(value: object, minimum: int = 0) -> bool:
    return type(value) is int and minimum <= value <= MAX_SAFE_INTEGER


def digest_value(value: object) -> bool:
    return isinstance(value, str) and HASH.fullmatch(value) is not None


def fingerprint(obj: object) -> bool:
    return (type(obj) is dict and set(obj) == {"sha256", "size"}
            and digest_value(obj["sha256"]) and safe_int(obj["size"]))


def canonical_demo_body(receipt: dict) -> bytes:
    body = {key: value for key, value in receipt.items()
            if key != "receipt_hash"}
    # The candidate schema deliberately limits all values to ASCII and safe
    # integers. For THIS restricted subset JSON sort_keys+compact formatting
    # agrees with JCS; this is not a general RFC 8785 implementation.
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    if not encoded.isascii():
        raise ValueError("illustrative subset contains non-ASCII")
    return encoded


def check_receipt(r: dict, previous: str | None) -> None:
    assert type(r) is dict and set(r) == RECEIPT_FIELDS, "top-level fields"
    assert r["format"] == "tombstone.receipt" and type(r["version"]) is int
    assert r["version"] == 1, "receipt format/version"
    assert r["kind"] in ("explicit-delete", "observed-transition", "unchanged")
    assert fingerprint(r["before"]) and fingerprint(r["after"])
    assert r["previous_receipt_hash"] == previous, "broken chain link"
    assert digest_value(r["receipt_hash"]), "bad receipt digest shape"
    if r["kind"] == "explicit-delete":
        d = r["deleted"]
        assert type(d) is dict and set(d) == {"sha256", "size", "offset"}
        assert digest_value(d["sha256"]) and safe_int(d["size"], 1)
        assert safe_int(d["offset"])
        assert d["size"] <= r["before"]["size"]
        assert d["offset"] <= r["before"]["size"] - d["size"]
    else:
        assert r["deleted"] is None, "non-witness deletion claimed"
        if r["kind"] == "unchanged":
            assert r["before"] == r["after"], "changed bytes marked unchanged"
        else:
            assert r["before"] != r["after"], "no-op marked changed"
    assert r["receipt_hash"] == sha(DOMAIN + canonical_demo_body(r)), \
        "receipt digest mismatch"


def check() -> None:
    expected = [
        "README.md", "ARCHITECTURE.md", "INVARIANTS.md", "AGENTS.md",
        "ROADMAP.md", "GETTING_STARTED.md", "SECURITY.md",
        "docs/INDEX.md", "docs/THREAT_MODEL.md",
        "machine/schemas/receipt-v1.schema.json",
        "docs/assets/tombstone-banner.svg",
    ]
    for path in expected:
        assert (ROOT / path).is_file(), "missing " + path

    ET.parse(ROOT / "docs/assets/tombstone-banner.svg")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert 'src="docs/assets/tombstone-banner.svg"' in readme
    assert "<h1" not in readme.lower() and not readme.startswith("# TOMBSTONE")

    schema = read_json(ROOT / "machine/schemas/receipt-v1.schema.json")
    assert schema["$schema"].endswith("2020-12/schema")
    assert schema["type"] == "object" and schema["additionalProperties"] is False
    assert set(schema["required"]) == RECEIPT_FIELDS
    assert set(schema["properties"]) == RECEIPT_FIELDS
    assert schema["properties"]["version"]["const"] == 1

    before = (ROOT / "tests/fixtures/before.txt").read_bytes()
    after = (ROOT / "tests/fixtures/after.txt").read_bytes()
    removed = (ROOT / "tests/fixtures/deleted.txt").read_bytes()
    assert before == b"1 2 3 4 5" and after == b"1 2 5"
    assert removed == b"3 4 " and before[:4] + before[8:] == after
    assert sha(b"") == ("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649"
                        "b934ca495991b7852b855")

    receipts = [read_json(ROOT / "machine/examples" / name) for name in ORDER]
    previous = None
    for receipt in receipts:
        check_receipt(receipt, previous)
        previous = receipt["receipt_hash"]

    explicit, observed, unchanged = receipts
    for receipt, expected_kind in zip(receipts,
            ("explicit-delete", "observed-transition", "unchanged")):
        assert receipt["kind"] == expected_kind
    assert explicit["before"] == observed["before"]
    assert explicit["after"] == observed["after"]
    assert explicit["before"] == {"sha256": sha(before), "size": len(before)}
    assert explicit["after"] == {"sha256": sha(after), "size": len(after)}
    assert explicit["deleted"] == {
        "sha256": sha(removed), "size": len(removed), "offset": 4}
    assert unchanged["before"] == unchanged["after"] == explicit["after"]

    # Sanity checks: document-only fixture validator rejects basic tampering.
    for mutation in ("bad-hash", "bad-chain", "fake-deletion", "extra-field"):
        bad = copy.deepcopy(observed)
        if mutation == "bad-hash":
            bad["receipt_hash"] = "0" * 64
        elif mutation == "bad-chain":
            bad["previous_receipt_hash"] = "0" * 64
        elif mutation == "fake-deletion":
            bad["deleted"] = {"sha256": sha(removed), "size": 4, "offset": 4}
        else:
            bad["deleted_text"] = "leak"
        try:
            check_receipt(bad, explicit["receipt_hash"])
        except AssertionError:
            pass
        else:
            raise AssertionError("negative case accepted: " + mutation)

    try:
        json.loads('{"version":1,"version":2}',
                   object_pairs_hook=reject_duplicate_keys)
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate key not rejected")

    print("PASS: TOMBSTONE docs, SVG, restricted receipt v1 vectors, "
          "toy bytes, chain and negative samples")
    print("NOTE: docs-only checker; the separate C99 receipt-v1 engine is tested "
          "by make test and does not implement arbitrary JSON Schema/JCS")


if __name__ == "__main__":
    check()
