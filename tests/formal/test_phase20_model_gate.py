#!/usr/bin/env python3
"""Regression tests for the acceptance boundary, independent of solver runtime."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tarfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_phase20_model_canary as gate


class ModelGate(unittest.TestCase):
    def outcome(self, code, text):
        return gate.verdict(subprocess.CompletedProcess([], code, text))

    def test_real_valid_shape(self):
        self.assertEqual(self.outcome(0, "\nunsat\n; Valid (0.1) (4 steps) (goal g_1)\n"), "VALID")

    def test_known_negative_timeout(self):
        value = self.outcome(142, "; Timeout (10)\n\ntimeout\n")
        gate.require_results({"false":value}, set(), {"false"})
        with self.assertRaises(ValueError):
            gate.require_results({"positive":value}, {"positive"})

    def test_contradiction_cannot_pass(self):
        for goal in gate.NEGATIVES:
            values = dict.fromkeys(gate.CONTROLS, "VALID")
            values.update(dict.fromkeys(gate.NEGATIVES, "NOT_PROVED"))
            values[goal] = "VALID"
            with self.subTest(goal=goal), self.assertRaises(ValueError):
                gate.require_results(values, gate.CONTROLS, gate.NEGATIVES)

    def test_no_missing_or_extra_goals(self):
        for values in ({}, {"positive":"VALID", "extra":"VALID"}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                gate.require_results(values, {"positive"})

    def test_no_arbitrary_negative_verdict(self):
        with self.assertRaises(ValueError):
            gate.require_results({"false":"SKIPPED"}, set(), {"false"})

    def test_tool_failures_are_not_negative_evidence(self):
        for code, text in ((1,"unknown\n"), (137,"timeout\n"), (0,""),
                           (0,"error: unknown\n"), (142,"unsat\n"),
                           (0,"unsat\n; Valid (1)\n; Valid (2)\n")):
            with self.subTest(code=code, text=text), self.assertRaises(ValueError):
                self.outcome(code,text)

    def test_pinned_patch_matches_manifest(self):
        spec = gate.model.spec()
        self.assertEqual(len(spec["files"]), 4)
        for row in spec["files"].values():
            self.assertNotEqual(row["original"],row["corrected"])

    def test_unbuilt_module_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(OSError):
                gate.model.check(Path(directory))

    def test_transport_and_model_drift(self):
        # Exercise the real integrity checker with a small synthetic tree;
        # this tests transport/integrity, not a mathematical model.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            (source / "share/why3").mkdir(parents=True)
            for name in ("MemBytes.ml", "wp.cmxs", "share/theory.mlw",
                         "share/.gitignore", "share/why3/.gitattributes"):
                (source / name).write_text("fixture: " + name + "\n")
            spec_path = root / "spec.json"
            spec_path.write_text("fixture spec\n")
            manifest = {"spec_sha256":gate.model.digest(spec_path),
                        "plugin_sha256":gate.model.digest(source / "wp.cmxs"),
                        "share_sha256":{str(p.relative_to(source)):gate.model.digest(p)
                                        for p in (source / "share").rglob("*") if p.is_file()}}
            (source / "build.json").write_text(json.dumps(manifest))
            specification = {"files":{"MemBytes.ml":{"corrected":gate.model.digest(source / "MemBytes.ml")}}}
            bundle = root / "model.tar.gz"
            with tarfile.open(bundle, "w:gz") as archive:
                archive.add(source, arcname="model")
            restored = root / "restored"
            restored.mkdir()
            with tarfile.open(bundle) as archive:
                archive.extractall(restored, filter="data")
            restored = restored / "model"
            with patch.object(gate.model, "SPEC", spec_path), patch.object(gate.model, "spec", return_value=specification):
                self.assertEqual(gate.model.check(source), gate.model.check(restored))
                for path in ("share/.gitignore", "share/why3/.gitattributes", "share/theory.mlw", "wp.cmxs"):
                    file = restored / path
                    original = file.read_bytes()
                    file.unlink()
                    with self.subTest(missing=path), self.assertRaises((ValueError, OSError)):
                        gate.model.check(restored)
                    file.write_bytes(original + b"changed")
                    with self.subTest(changed=path), self.assertRaises(ValueError):
                        gate.model.check(restored)
                    file.write_bytes(original)
                (restored / "share/unrecorded.mlw").write_text("extra")
                with self.assertRaises(ValueError):
                    gate.model.check(restored)


if __name__ == "__main__":
    unittest.main()
