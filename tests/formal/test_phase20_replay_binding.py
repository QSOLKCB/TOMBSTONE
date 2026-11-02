#!/usr/bin/env python3
"""Keep orchestration changes from silently renewing historical proof inputs."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_phase20_replay_binding as binding


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.history = json.loads((ROOT / binding.HISTORY).read_text())
        self.record = json.loads((ROOT / binding.RECORD).read_text())
        for name in set(self.history["source_blobs"]) | binding.ADDED | {binding.RECORD, binding.HISTORY}:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)

    def validate(self):
        binding.validate(self.history["source_blobs"], self.root)

    def save(self):
        (self.root / binding.RECORD).write_text(json.dumps(self.record))

    def test_current_binding_accepts_without_changing_history(self):
        self.validate()
        self.assertEqual((self.root / binding.HISTORY).read_bytes(), (ROOT / binding.HISTORY).read_bytes())

    def test_every_original_proof_input_stays_pinned(self):
        for name in set(self.history["source_blobs"]) - binding.REPLACED:
            path = self.root / name
            original = path.read_bytes()
            path.write_bytes(original + b"changed")
            with self.subTest(path=name), self.assertRaisesRegex(ValueError, "stale proof dependency"):
                self.validate()
            path.write_bytes(original)

    def test_every_new_or_replaced_dependency_stays_pinned(self):
        for name in binding.ADDED | binding.REPLACED:
            path = self.root / name
            original = path.read_bytes()
            path.write_bytes(original + b"changed")
            with self.subTest(path=name), self.assertRaisesRegex(ValueError, "stale proof dependency"):
                self.validate()
            path.write_bytes(original)

    def test_proof_input_cannot_be_added_to_ci_exception(self):
        name = "src/encoding/receipt.c"
        path = self.root / name
        path.write_bytes(path.read_bytes() + b"changed")
        self.record["current_blobs"][name] = binding.git_blob(path.read_bytes())
        self.save()
        with self.assertRaisesRegex(ValueError, "unexpected replay dependency"):
            self.validate()

    def test_historical_execution_cannot_be_relabelled(self):
        altered = copy.deepcopy(self.history)
        altered["workflow_conclusion"] = "success"
        (self.root / binding.HISTORY).write_text(json.dumps(altered))
        with self.assertRaisesRegex(ValueError, "historical Phase 20 evidence changed"):
            self.validate()

    def test_supplied_historical_dependency_map_cannot_change(self):
        self.history["source_blobs"]["src/encoding/receipt.c"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "stale proof dependency"):
            self.validate()

    def test_unknown_missing_and_promoted_fields_rejected(self):
        base = copy.deepcopy(self.record)
        for key, value in (("version", True), ("version", 2), ("scope", "PROVED"),
                           ("historical_sha256", "0" * 64), ("unknown", 1), ("current_blobs", {})):
            self.record = dict(base, **{key: value})
            self.save()
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate()

    def test_duplicate_keys_rejected(self):
        path = self.root / binding.RECORD
        path.write_text(path.read_text().replace('"version": 1', '"version": 1, "version": 1'))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.validate()

    def test_alias_cannot_satisfy_dependency(self):
        name = next(iter(binding.ADDED))
        path = self.root / name
        target = self.root / "aliased-copy"
        path.rename(target)
        path.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "aliased replay dependency"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
