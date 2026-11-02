#!/usr/bin/env python3
"""Restore one independently pinned WP build; never cache proof results."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import stat
import sys
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

import phase20_model as model

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = "machine/formal/phase20-toolchain-reuse-v1.json"
IMAGE = "framac/frama-c:32.1@sha256:4f0b7a2bd600c4daabfdcdfa393a3c18301e0db18f3b2739f1d9650193462d36"
REPOSITORY = "QSOLKCB/TOMBSTONE"
BUILD_INPUTS = {"tools/phase20_model.py", "machine/formal/phase20-model-correction-v1.json",
                "formal/framac/toolchain/phase20-bytes.patch"}
POLICY_INPUTS = {"tools/phase20_toolchain_reuse.py", "tests/formal/test_phase20_toolchain_reuse.py",
                 "tests/formal/run_phase20_model_canary.py", "tests/formal/phase20_bytes_model_canary.mlw",
                 "tests/formal/phase20_model_copy_regressions.mlw", "tests/formal/phase20_model_readonly.c",
                 "tools/phase20_receipt_overlay.py", "tests/formal/test_phase20_model_gate.py"}
POLICY_INPUTS |= {".github/workflows/phase20-receipt-prerequisites.yml",
                  ".github/workflows/phase20-toolchain-reuse-benchmark.yml",
                  "tools/benchmark_phase20_toolchain.py"}
ZIP_LIMIT = 8 * 1024 * 1024
TREE_LIMIT = 32 * 1024 * 1024
FILE_LIMIT = 256


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def load(data):
    return json.loads(data, object_pairs_hook=unique)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def file_bytes(path):
    # Inputs and cache entries must be regular files, not aliases.
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError("missing or nonregular input: " + str(path))
    return path.read_bytes()


def anchor(root=ROOT):
    value = load(file_bytes(root / RECEIPT))
    if set(value) != {"format", "version", "image", "platform", "build_inputs", "policy_inputs",
                      "producer", "artifact", "files_sha256"}:
        raise ValueError("unknown or missing toolchain receipt field")
    if value["format"] != "tombstone.phase20.verified-toolchain" or type(value["version"]) is not int or value["version"] != 1:
        raise ValueError("unknown toolchain receipt version")
    if value["image"] != IMAGE or value["platform"] != "linux/amd64":
        raise ValueError("toolchain image or platform mismatch")
    if set(value["build_inputs"]) != BUILD_INPUTS or set(value["policy_inputs"]) != POLICY_INPUTS:
        raise ValueError("incomplete toolchain dependency closure")
    producer = value["producer"]
    if set(producer) != {"repository", "repository_id", "run_id", "run_attempt", "head_sha", "event", "branch", "workflow"}:
        raise ValueError("invalid producer fields")
    if (producer["repository"], producer["repository_id"], producer["event"], producer["branch"], producer["workflow"]) != (
            REPOSITORY, 1441527695, "push", "main", ".github/workflows/phase20-receipt-prerequisites.yml"):
        raise ValueError("untrusted toolchain producer")
    artifact = value["artifact"]
    if set(artifact) != {"id", "name", "zip_sha256", "zip_bytes", "tar_sha256", "tar_bytes", "file_count", "tree_bytes", "plugin_sha256"}:
        raise ValueError("invalid artifact fields")
    if artifact["name"] != "phase20-corrected-toolchain":
        raise ValueError("wrong artifact name")
    for number in (producer["run_id"], producer["run_attempt"], artifact["id"], artifact["zip_bytes"],
                   artifact["tar_bytes"], artifact["file_count"], artifact["tree_bytes"]):
        if type(number) is not int or number <= 0:
            raise ValueError("invalid artifact count or identity")
    if artifact["zip_bytes"] > ZIP_LIMIT or artifact["tar_bytes"] > ZIP_LIMIT or artifact["tree_bytes"] > TREE_LIMIT or artifact["file_count"] > FILE_LIMIT:
        raise ValueError("artifact exceeds resource limits")
    hashes = [*value["build_inputs"].values(), *value["policy_inputs"].values(), *value["files_sha256"].values(),
              artifact["zip_sha256"], artifact["tar_sha256"], artifact["plugin_sha256"]]
    if any(not isinstance(h, str) or len(h) != 64 or any(c not in "0123456789abcdef" for c in h) for h in hashes):
        raise ValueError("invalid digest")
    if not isinstance(producer["head_sha"], str) or len(producer["head_sha"]) != 40 or any(c not in "0123456789abcdef" for c in producer["head_sha"]):
        raise ValueError("invalid producer commit")
    if len(value["files_sha256"]) != artifact["file_count"]:
        raise ValueError("incomplete artifact file inventory")
    for name in value["files_sha256"]:
        safe_name(name)
    if not {"build.json", "wp.cmxs", "MemBytes.ml"} <= set(value["files_sha256"]):
        raise ValueError("missing model files")
    return value


def identity(root=ROOT, force_cold=False):
    value = anchor(root)
    if (platform.system(), platform.machine()) != ("Linux", "x86_64"):
        raise ValueError("unsupported toolchain host; require Linux x86_64")
    current = {name: sha(file_bytes(root / name)) for name in sorted(BUILD_INPUTS | POLICY_INPUTS)}
    expected = value["build_inputs"] | value["policy_inputs"]
    changed = sorted(name for name in current if current[name] != expected[name])
    key = "phase20-toolchain-v1-" + sha(canonical({"receipt": value, "inputs": current, "image": IMAGE, "platform": "linux/amd64"}))
    return value, {"key": key, "eligible": not force_cold and not changed,
                   "reason": "FORCED_COLD" if force_cold else "INPUTS_CHANGED" if changed else "EXACT_INPUTS",
                   "changed_inputs": changed, "input_sha256": current}


def safe_name(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or ".." in p.parts or "\\" in name or str(p) != name or name == ".":
        raise ValueError("unsafe or noncanonical archive path")
    return p


def unpack(data, value, output):
    """Verify in-memory bytes against the outside receipt before extracting."""
    a = value["artifact"]
    if len(data) != a["zip_bytes"] or len(data) > ZIP_LIMIT or sha(data) != a["zip_sha256"]:
        raise ValueError("approved ZIP identity mismatch")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        rows = archive.infolist()
        if len(rows) != 1 or rows[0].filename != "phase20-corrected-toolchain.tar.gz" or rows[0].file_size != a["tar_bytes"] or rows[0].flag_bits & 1:
            raise ValueError("unexpected ZIP inventory")
        if stat.S_ISLNK(rows[0].external_attr >> 16):
            raise ValueError("ZIP symlink rejected")
        packed = archive.read(rows[0])
    if sha(packed) != a["tar_sha256"]:
        raise ValueError("approved tar identity mismatch")
    files = {}
    seen = set()
    total = 0
    with tarfile.open(fileobj=io.BytesIO(packed), mode="r:gz") as archive:
        for member in archive:
            if member.name in (".", "./") and member.isdir():
                continue
            name = member.name.removeprefix("./")
            safe_name(name)
            if name in seen or len(seen) >= FILE_LIMIT * 2:
                raise ValueError("duplicate or excessive tar members")
            seen.add(name)
            if member.isdir():
                continue
            if not member.isfile() or member.size < 0:
                raise ValueError("nonregular tar member")
            total += member.size
            if total > TREE_LIMIT or len(files) >= FILE_LIMIT:
                raise ValueError("expanded model exceeds resource limits")
            content = archive.extractfile(member).read(member.size + 1)
            if len(content) != member.size:
                raise ValueError("truncated tar member")
            files[name] = content
    if total != a["tree_bytes"] or {n: sha(b) for n, b in files.items()} != value["files_sha256"]:
        raise ValueError("model tree differs from independently pinned manifest")
    if sha(files["wp.cmxs"]) != a["plugin_sha256"]:
        raise ValueError("wrong model plugin")
    # A fresh private destination has no mutable shared-cache aliases. It is
    # not published as reusable state; CI publishes only after fresh canaries.
    output.mkdir()
    for name, content in files.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        path.chmod(0o444)
    model.check(output)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HTTPSRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        checked_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def checked_url(url):
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https" or not p.hostname or p.username or p.password:
        raise ValueError("unsafe artifact redirect")


def api(path, redirect=False):
    request = urllib.request.Request("https://api.github.com/repos/" + REPOSITORY + path,
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"], "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "TOMBSTONE-phase20-toolchain"})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=60) as response:
            data = response.read(1024 * 1024 + 1)
            if len(data) > 1024 * 1024:
                raise ValueError("API response exceeds limit")
            if redirect:
                raise ValueError("artifact endpoint did not redirect")
            return load(data)
    except urllib.error.HTTPError as error:
        if error.code in (404, 410):
            raise FileNotFoundError("approved artifact or producer unavailable") from None
        if redirect and error.code == 302:
            location = error.headers["Location"]
            checked_url(location)
            return location
        raise ValueError("GitHub API HTTP " + str(error.code)) from None
    except urllib.error.URLError:
        raise ValueError("GitHub API network failure") from None


def fetch(value):
    p, a = value["producer"], value["artifact"]
    run = api(f"/actions/runs/{p['run_id']}/attempts/{p['run_attempt']}")
    if (run["id"], run["run_attempt"], run["event"], run["head_branch"], run["head_sha"],
        run["status"], run["conclusion"], run["path"], run["repository"]["id"], run["head_repository"]["id"]) != (
            p["run_id"], p["run_attempt"], "push", "main", p["head_sha"], "completed", "success",
            p["workflow"], p["repository_id"], p["repository_id"]):
        raise ValueError("producer provenance mismatch")
    meta = api(f"/actions/artifacts/{a['id']}")
    origin = meta["workflow_run"]
    if (meta["id"], meta["name"], meta["digest"], meta["size_in_bytes"], origin["id"], origin["head_sha"],
        origin["head_branch"], origin["repository_id"], origin["head_repository_id"]) != (
            a["id"], a["name"], "sha256:" + a["zip_sha256"], a["zip_bytes"], p["run_id"], p["head_sha"],
            "main", p["repository_id"], p["repository_id"]):
        raise ValueError("artifact provenance mismatch")
    if meta["expired"] is True:
        raise FileNotFoundError("approved artifact expired")
    if meta["expired"] is not False:
        raise ValueError("invalid artifact expiration state")
    url = api(f"/actions/artifacts/{a['id']}/zip", redirect=True)
    # Never forward GH_TOKEN to the signed storage URL or its redirects.
    try:
        with urllib.request.build_opener(HTTPSRedirect()).open(url, timeout=60) as response:
            data = response.read(ZIP_LIMIT + 1)
    except (urllib.error.HTTPError, urllib.error.URLError):
        raise ValueError("artifact storage download failed") from None
    if len(data) > ZIP_LIMIT:
        raise ValueError("artifact download exceeds limit")
    return data


def acquire(output, archive, root=ROOT, force_cold=False, expected_key=None):
    started = time.monotonic()
    for path in (output, archive):
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("model or cache path must not be a symlink")
    value, state = identity(root, force_cold)
    if expected_key is not None and state["key"] != expected_key:
        raise ValueError("input snapshot changed after cache selection")
    if output.exists() or output.is_symlink():
        raise ValueError("model destination must be new")
    report = {"format": "tombstone.phase20.toolchain-preparation", "version": 1,
              "key": state["key"], "input_sha256": state["input_sha256"],
              "mode": "COLD_BUILD_REQUIRED", "build_completed": False, "reason": state["reason"],
              "proof_results_reused": False, "producer": None, "archive_source": None}
    if state["eligible"]:
        if archive.is_symlink():
            raise ValueError("cache archive must not be a symlink")
        if archive.exists():
            if archive.stat().st_size > ZIP_LIMIT:
                raise ValueError("cache archive exceeds limit")
            data = file_bytes(archive)
            source = "VERIFIED_CACHE"
        else:
            try:
                data = fetch(value)
            except FileNotFoundError:
                report["reason"] = "APPROVED_ARTIFACT_UNAVAILABLE"
                data = None
            source = "PINNED_GITHUB_ARTIFACT"
        if data is not None:
            unpack(data, value, output)
            if not archive.exists():
                archive.parent.mkdir(parents=True, exist_ok=True)
                with archive.open("xb") as stream:
                    stream.write(data)
            report.update(mode="REUSED_VERIFIED_TOOLCHAIN", build_completed=True,
                          producer=value["producer"], archive_source=source,
                          plugin_sha256=value["artifact"]["plugin_sha256"], reason="EXACT_INPUTS_AND_ARTIFACT")
    report["acquisition_seconds"] = time.monotonic() - started
    return report


def complete(report, output, canary, root=ROOT):
    _, state = identity(root)
    if state["key"] != report["key"] or state["input_sha256"] != report["input_sha256"]:
        raise ValueError("input snapshot changed during model preparation")
    built = model.check(output)
    result = load(file_bytes(canary))
    if result["format"] != "tombstone.phase20.corrected-model-regressions" or type(result["version"]) is not int or result["version"] != 1 or result["status"] != "CANARY_PASSED_NOT_A_SOUNDNESS_PROOF" or result["build"] != built:
        raise ValueError("fresh canary identity or execution mismatch")
    if set(result["outcomes"]) != {"original", "corrected", "copy_regressions", "library_lemmas", "readonly", "string_lemma"}:
        raise ValueError("missing canary family")
    if report["mode"] not in ("COLD_BUILD_REQUIRED", "REUSED_VERIFIED_TOOLCHAIN") or report["proof_results_reused"] is not False:
        raise ValueError("invalid preparation state")
    if report["mode"] == "REUSED_VERIFIED_TOOLCHAIN" and built["plugin_sha256"] != report["plugin_sha256"]:
        raise ValueError("validated model replaced before use")
    report.update(build_completed=True, plugin_sha256=built["plugin_sha256"],
                  canary_execution="EXECUTED_FRESH", canary_result_sha256=sha(file_bytes(canary)))
    if report["mode"] == "COLD_BUILD_REQUIRED":
        report["mode"] = "EXECUTED_FRESH"
    return report


def emit_outputs(values, path):
    if path:
        with Path(path).open("a") as stream:
            for key, value in values.items():
                stream.write(f"{key}={str(value).lower() if type(value) is bool else value}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("key", "acquire", "complete"))
    ap.add_argument("--force-cold", action="store_true")
    ap.add_argument("--output", type=Path)
    ap.add_argument("--archive", type=Path, default=Path("phase20-cache/approved.zip"))
    ap.add_argument("--report", type=Path, default=Path("phase20-model-results/preparation.json"))
    ap.add_argument("--canary", type=Path)
    ap.add_argument("--expected-key")
    ap.add_argument("--github-output")
    args = ap.parse_args()
    if args.action == "key":
        _, state = identity(force_cold=args.force_cold)
        emit_outputs({k: state[k] for k in ("key", "eligible")}, args.github_output)
        print(json.dumps(state, sort_keys=True))
        return
    if args.output is None:
        ap.error("--output is required")
    if args.action == "acquire":
        report = acquire(args.output, args.archive, force_cold=args.force_cold, expected_key=args.expected_key)
        emit_outputs({"mode": report["mode"], "needs_build": not report["build_completed"]}, args.github_output)
    else:
        if args.canary is None:
            ap.error("--canary is required")
        report = complete(load(file_bytes(args.report)), args.output, args.canary)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, tarfile.TarError, zipfile.BadZipFile) as error:
        raise SystemExit("FAIL: Phase 20 toolchain reuse: " + str(error)) from error
