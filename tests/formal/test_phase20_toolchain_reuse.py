#!/usr/bin/env python3
"""Offline adversarial reuse tests; no solver success is simulated or claimed."""
import copy
import io
import json
from pathlib import Path
import stat
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import phase20_toolchain_reuse as reuse


def bundle(files, extra=(), zip_name="phase20-corrected-toolchain.tar.gz"):
    packed = io.BytesIO()
    with tarfile.open(fileobj=packed, mode="w:gz") as archive:
        for name, data in files.items():
            member = tarfile.TarInfo("./" + name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
        for member, data in extra:
            archive.addfile(member, io.BytesIO(data))
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr(zip_name, packed.getvalue())
    return data.getvalue(), packed.getvalue()


class ReuseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in reuse.BUILD_INPUTS | reuse.POLICY_INPUTS:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(name.encode())
        spec_path = self.root / "machine/formal/phase20-model-correction-v1.json"
        patch_path = self.root / "formal/framac/toolchain/phase20-bytes.patch"
        self.files = {"wp.cmxs": b"synthetic parser fixture, not an executable",
                      "MemBytes.ml": b"synthetic model", "share/why3/core.mlw": b"synthetic theory",
                      "share/.hidden": b"included"}
        spec = {"patch_sha256": reuse.sha(patch_path.read_bytes()), "files": {
            name: {"corrected": reuse.sha(data)} for name, data in self.files.items()
            if name in ("MemBytes.ml", "share/why3/core.mlw")}}
        spec_path.write_text(json.dumps(spec))
        self.build = {"spec_sha256": reuse.sha(spec_path.read_bytes()),
                      "plugin_sha256": reuse.sha(self.files["wp.cmxs"]),
                      "share_sha256": {n: reuse.sha(b) for n, b in self.files.items() if n.startswith("share/")}}
        self.files["build.json"] = json.dumps(self.build).encode()
        self.value = {"format": "tombstone.phase20.verified-toolchain", "version": 1,
                      "image": reuse.IMAGE, "platform": "linux/amd64",
                      "build_inputs": {n: reuse.sha((self.root / n).read_bytes()) for n in reuse.BUILD_INPUTS},
                      "policy_inputs": {n: reuse.sha((self.root / n).read_bytes()) for n in reuse.POLICY_INPUTS},
                      "producer": {"repository": reuse.REPOSITORY, "repository_id": 1441527695,
                                   "run_id": 123, "run_attempt": 1, "head_sha": "a" * 40,
                                   "event": "push", "branch": "main",
                                   "workflow": ".github/workflows/phase20-receipt-prerequisites.yml"}}
        self.repack()
        self.output = self.root / "model"
        self.cache = self.root / "cache/approved.zip"
        for name, value in (("SPEC", spec_path), ("PATCH", patch_path)):
            p = patch.object(reuse.model, name, value)
            p.start()
            self.addCleanup(p.stop)

    def repack(self, extra=(), zip_name="phase20-corrected-toolchain.tar.gz"):
        self.data, packed = bundle(self.files, extra, zip_name)
        self.value["artifact"] = {"id": 456, "name": "phase20-corrected-toolchain",
            "zip_sha256": reuse.sha(self.data), "zip_bytes": len(self.data),
            "tar_sha256": reuse.sha(packed), "tar_bytes": len(packed),
            "file_count": len(self.files), "tree_bytes": sum(map(len, self.files.values())),
            "plugin_sha256": reuse.sha(self.files["wp.cmxs"])}
        self.value["files_sha256"] = {n: reuse.sha(b) for n, b in self.files.items()}
        self.save()

    def save(self):
        (self.root / reuse.RECEIPT).write_text(json.dumps(self.value))

    def cached(self):
        self.cache.parent.mkdir()
        self.cache.write_bytes(self.data)

    def acquire(self, **options):
        return reuse.acquire(self.output, self.cache, self.root, **options)

    def test_valid_cache_needs_fresh_canary(self):
        self.cached()
        with patch.object(reuse, "fetch", side_effect=AssertionError("network on hit")):
            report = self.acquire()
        self.assertEqual(report["mode"], "REUSED_VERIFIED_TOOLCHAIN")
        self.assertEqual(report["archive_source"], "VERIFIED_CACHE")
        self.assertFalse(report["proof_results_reused"])
        self.assertNotIn("canary_execution", report)
        self.assertEqual((self.output / "share/.hidden").read_bytes(), b"included")
        self.assertFalse((self.output / "wp.cmxs").stat().st_mode & stat.S_IWUSR)

    def test_verified_download_saved_as_exact_archive(self):
        with patch.object(reuse, "fetch", return_value=self.data):
            report = self.acquire()
        self.assertEqual(report["archive_source"], "PINNED_GITHUB_ARTIFACT")
        self.assertEqual(self.cache.read_bytes(), self.data)

    def test_forced_cold_bypasses_even_corrupt_cache(self):
        self.cached()
        self.cache.write_bytes(b"corrupt")
        with patch.object(reuse, "fetch", side_effect=AssertionError("network on forced cold")):
            report = self.acquire(force_cold=True)
        self.assertEqual(report["mode"], "COLD_BUILD_REQUIRED")
        self.assertFalse(report["build_completed"])
        self.assertFalse(self.output.exists())

    def test_every_build_and_policy_input_invalidates_key(self):
        key = reuse.identity(self.root)[1]["key"]
        for name in reuse.BUILD_INPUTS | reuse.POLICY_INPUTS:
            path = self.root / name
            old = path.read_bytes()
            path.write_bytes(old + b"changed")
            with self.subTest(path=name):
                state = reuse.identity(self.root)[1]
                self.assertFalse(state["eligible"])
                self.assertNotEqual(state["key"], key)
                with patch.object(reuse, "fetch", side_effect=AssertionError("stale reuse")):
                    self.assertEqual(self.acquire()["reason"], "INPUTS_CHANGED")
            path.write_bytes(old)

    def test_snapshot_change_between_key_and_acquire(self):
        key = reuse.identity(self.root)[1]["key"]
        (self.root / "tools/phase20_model.py").write_text("changed")
        with self.assertRaisesRegex(ValueError, "snapshot changed"):
            self.acquire(expected_key=key)

    def test_unavailable_artifact_falls_back_without_output(self):
        with patch.object(reuse, "fetch", side_effect=FileNotFoundError):
            report = self.acquire()
        self.assertEqual(report["reason"], "APPROVED_ARTIFACT_UNAVAILABLE")
        self.assertFalse(self.output.exists())
        self.assertFalse(self.cache.exists())

    def test_integrity_and_permission_errors_do_not_fall_back(self):
        for error in (ValueError("provenance mismatch"), PermissionError("forbidden")):
            with patch.object(reuse, "fetch", side_effect=error), self.assertRaises(type(error)):
                self.acquire()

    def test_corrupt_cache_is_rejected_not_redownloaded(self):
        self.cached()
        self.cache.write_bytes(self.data[:-1])
        with patch.object(reuse, "fetch", side_effect=AssertionError("masked corruption")), self.assertRaisesRegex(ValueError, "ZIP identity"):
            self.acquire()
        self.assertFalse(self.output.exists())

    def test_self_consistent_internal_manifest_cannot_authorize_payload(self):
        altered = dict(self.files)
        altered["wp.cmxs"] = b"untrusted"
        built = dict(self.build, plugin_sha256=reuse.sha(altered["wp.cmxs"]))
        altered["build.json"] = json.dumps(built).encode()
        data, packed = bundle(altered)
        value = copy.deepcopy(self.value)
        # Even a newly supplied transport digest cannot replace the outside file inventory.
        value["artifact"].update(zip_sha256=reuse.sha(data), zip_bytes=len(data),
                                 tar_sha256=reuse.sha(packed), tar_bytes=len(packed))
        with self.assertRaisesRegex(ValueError, "independently pinned manifest"):
            reuse.unpack(data, value, self.output)

    def test_bad_tar_digest(self):
        self.value["artifact"]["tar_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "tar identity"):
            reuse.unpack(self.data, self.value, self.output)

    def test_archive_rejects_traversal_absolute_duplicates_links_and_devices(self):
        for name, kind in (("../escape", tarfile.REGTYPE), ("/escape", tarfile.REGTYPE),
                           ("./wp.cmxs", tarfile.REGTYPE), ("alias", tarfile.SYMTYPE),
                           ("hard", tarfile.LNKTYPE), ("fifo", tarfile.FIFOTYPE),
                           ("a\\b", tarfile.REGTYPE)):
            with self.subTest(name=name):
                row = tarfile.TarInfo(name)
                row.type = kind
                row.linkname = "wp.cmxs"
                self.repack(((row, b""),))
                with self.assertRaises(ValueError):
                    reuse.unpack(self.data, self.value, self.output)
                self.assertFalse(self.output.exists())

    def test_zip_inventory_rejected(self):
        self.repack(zip_name="other.tar.gz")
        with self.assertRaisesRegex(ValueError, "ZIP inventory"):
            reuse.unpack(self.data, self.value, self.output)

    def test_unexpected_file_and_missing_hidden_file(self):
        for name, value in (("extra", b"extra"), ("share/.hidden", None)):
            files = dict(self.files)
            if value is None:
                files.pop(name)
            else:
                files[name] = value
            data, packed = bundle(files)
            receipt = copy.deepcopy(self.value)
            receipt["artifact"].update(zip_sha256=reuse.sha(data), zip_bytes=len(data),
                                       tar_sha256=reuse.sha(packed), tar_bytes=len(packed))
            with self.assertRaisesRegex(ValueError, "independently pinned manifest"):
                reuse.unpack(data, receipt, self.output)

    def test_model_checker_remains_mandatory(self):
        self.files["MemBytes.ml"] = b"wrong model"
        self.repack()
        with self.assertRaisesRegex(ValueError, "corrected model identity"):
            reuse.unpack(self.data, self.value, self.output)

    def test_existing_destination_rejected(self):
        self.output.mkdir()
        with self.assertRaisesRegex(ValueError, "destination must be new"):
            self.acquire()

    def test_input_and_cache_aliases_rejected(self):
        source = self.root / "tools/phase20_model.py"
        original = source.read_bytes()
        source.unlink()
        source.symlink_to(self.root / "tools/phase20_toolchain_reuse.py")
        with self.assertRaisesRegex(ValueError, "nonregular"):
            reuse.identity(self.root)
        source.unlink()
        source.write_bytes(original)
        self.cache.parent.mkdir()
        self.cache.symlink_to(source)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.acquire()

    def test_parent_alias_rejected(self):
        alias = self.root / "aliased"
        alias.symlink_to(self.root / "tools", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "nonregular"):
            reuse.file_bytes(alias / "phase20_model.py")
        with self.assertRaisesRegex(ValueError, "symlink"):
            reuse.acquire(alias / "new-model", self.cache, self.root)
        with self.assertRaisesRegex(ValueError, "symlink"):
            reuse.acquire(self.output, alias / "new-cache.zip", self.root)

    def test_receipt_rejects_unknown_version_fields_and_missing_dependencies(self):
        base = copy.deepcopy(self.value)
        mutations = [("version", True), ("version", 2), ("unknown", 0),
                     ("image", "mutable:tag"), ("platform", "linux/arm64"),
                     ("build_inputs", {}), ("policy_inputs", {}), ("files_sha256", {})]
        for key, value in mutations:
            self.value = copy.deepcopy(base)
            self.value[key] = value
            self.save()
            with self.subTest(key=key), self.assertRaises(ValueError):
                reuse.anchor(self.root)

    def test_receipt_limits_and_boolean_identity_rejected(self):
        for key, number in (("zip_bytes", reuse.ZIP_LIMIT + 1), ("tree_bytes", reuse.TREE_LIMIT + 1),
                            ("file_count", reuse.FILE_LIMIT + 1), ("id", True)):
            saved = self.value["artifact"][key]
            self.value["artifact"][key] = number
            self.save()
            with self.assertRaises(ValueError):
                reuse.anchor(self.root)
            self.value["artifact"][key] = saved

    def test_duplicate_receipt_fields_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            reuse.load('{"version":1,"version":1}')

    def producer_records(self):
        p, a = self.value["producer"], self.value["artifact"]
        run = {"id": p["run_id"], "run_attempt": 1, "event": "push", "head_branch": "main",
               "head_sha": p["head_sha"], "status": "completed", "conclusion": "success",
               "path": p["workflow"], "repository": {"id": p["repository_id"]},
               "head_repository": {"id": p["repository_id"]}}
        meta = {"id": a["id"], "name": a["name"], "digest": "sha256:" + a["zip_sha256"],
                "size_in_bytes": a["zip_bytes"], "expired": False,
                "workflow_run": {"id": p["run_id"], "head_sha": p["head_sha"], "head_branch": "main",
                                 "repository_id": p["repository_id"], "head_repository_id": p["repository_id"]}}
        return run, meta

    def test_wrong_failed_pr_fork_or_attempt_producer_rejected(self):
        for field, value in (("id", 999), ("run_attempt", 2), ("event", "pull_request"),
                             ("conclusion", "failure"), ("status", "in_progress"),
                             ("head_branch", "feature"), ("head_sha", "b" * 40),
                             ("head_repository", {"id": 99}), ("path", "other.yml")):
            run, _ = self.producer_records()
            run[field] = value
            with patch.object(reuse, "api", return_value=run), self.assertRaisesRegex(ValueError, "producer provenance"):
                reuse.fetch(self.value)

    def test_wrong_artifact_provenance_rejected(self):
        for field, value in (("id", 999), ("name", "other"), ("digest", "sha256:" + "0" * 64),
                             ("size_in_bytes", 1)):
            run, meta = self.producer_records()
            meta[field] = value
            with patch.object(reuse, "api", side_effect=[run, meta]), self.assertRaisesRegex(ValueError, "artifact provenance"):
                reuse.fetch(self.value)
        run, meta = self.producer_records()
        meta["workflow_run"]["head_repository_id"] = 99
        with patch.object(reuse, "api", side_effect=[run, meta]), self.assertRaisesRegex(ValueError, "artifact provenance"):
            reuse.fetch(self.value)

    def test_expired_artifact_is_miss(self):
        run, meta = self.producer_records()
        meta["expired"] = True
        with patch.object(reuse, "api", side_effect=[run, meta]), self.assertRaises(FileNotFoundError):
            reuse.fetch(self.value)

    def test_unsafe_redirects_rejected(self):
        for url in ("http://example.com/a", "https://user:password@example.com/a", "file:///tmp/a", "//example.com/a"):
            with self.assertRaises(ValueError):
                reuse.checked_url(url)

    def test_completion_rejects_partial_or_different_canary(self):
        self.cached()
        report = self.acquire()
        canary = self.root / "result.json"
        base = {"format": "tombstone.phase20.corrected-model-regressions", "version": 1,
                "build": self.build, "outcomes": {n: {} for n in (
                    "original", "corrected", "copy_regressions", "library_lemmas", "readonly", "string_lemma")},
                "status": "CANARY_PASSED_NOT_A_SOUNDNESS_PROOF"}
        # Parser fixtures exercise identity checks, never count as executed canaries.
        for key, value in (("status", "LOCAL_THEORY_DIAGNOSTICS_ONLY"), ("build", {}), ("outcomes", {}), ("version", True)):
            altered = dict(base, **{key: value})
            canary.write_text(json.dumps(altered))
            with self.assertRaises(ValueError):
                reuse.complete(copy.deepcopy(report), self.output, canary, self.root)
        canary.write_text(json.dumps(base))
        (self.root / "tools/phase20_model.py").write_text("changed")
        with self.assertRaisesRegex(ValueError, "snapshot changed"):
            reuse.complete(report, self.output, canary, self.root)


if __name__ == "__main__":
    unittest.main()
