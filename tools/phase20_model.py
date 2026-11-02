#!/usr/bin/env python3
"""Build and identify the explicit Phase 20 WP correction in an isolated directory.

The upstream installation is never overwritten. All other phases keep their
original toolchain; compatibility replays use this entry point explicitly.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "machine/formal/phase20-model-correction-v1.json"
PATCH = ROOT / "formal/framac/toolchain/phase20-bytes.patch"
INSTALLED = Path("/home/opam/.opam/4.14/share/frama-c/share/wp")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def spec():
    value = json.loads(SPEC.read_text())
    if value["patch_sha256"] != digest(PATCH):
        raise ValueError("model patch identity changed")
    return value


def check(output):
    value = spec()
    receipt = json.loads((output / "build.json").read_text())
    if receipt["spec_sha256"] != digest(SPEC):
        raise ValueError("model build uses a different correction")
    if receipt["plugin_sha256"] != digest(output / "wp.cmxs"):
        raise ValueError("model plugin changed after build")
    for name, hashes in value["files"].items():
        path = output / (name if name == "MemBytes.ml" else name)
        if digest(path) != hashes["corrected"]:
            raise ValueError("corrected model identity mismatch: " + name)
    # The complete share tree, not only the edited theories, is part of the build.
    current = {str(p.relative_to(output)): digest(p)
               for p in sorted((output / "share").rglob("*")) if p.is_file()}
    if current != receipt["share_sha256"]:
        raise ValueError("WP share tree changed after build")
    return receipt


def build(output, archive):
    value = spec()
    output.mkdir()  # No reuse of stale binaries or theory files.
    with tempfile.TemporaryDirectory(prefix="phase20-wp-") as temp:
        temp = Path(temp)
        if archive is None:
            archive = temp / "upstream.tar.gz"
            urllib.request.urlretrieve(value["archive_url"], archive)
        if digest(archive) != value["archive_sha256"]:
            raise ValueError("upstream source archive identity mismatch")
        source = temp / "source"
        source.mkdir()
        with tarfile.open(archive) as bundle:
            for member in bundle:
                if not member.name.startswith(value["archive_prefix"]):
                    continue
                relative = Path(member.name[len(value["archive_prefix"]):])
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError("unsafe archive member")
                target = source / relative
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(bundle.extractfile(member).read())
                else:
                    raise ValueError("unexpected archive member type")
        for name, hashes in value["files"].items():
            if digest(source / name) != hashes["original"]:
                raise ValueError("upstream source identity mismatch: " + name)
            if name.startswith("share/") and digest(INSTALLED / name[6:]) != hashes["original"]:
                raise ValueError("installed original model differs from pinned source")
        subprocess.run(["patch", "--batch", "--fuzz=0", "-p1", "-i", str(PATCH)],
                       cwd=source, check=True)
        for name, hashes in value["files"].items():
            if digest(source / name) != hashes["corrected"]:
                raise ValueError("patched source identity mismatch: " + name)
        (source / "dune-project").write_text(
            "(lang dune 3.14)\n(using dune_site 0.1)\n(name frama-c-wp)\n"
            "(package (name frama-c-wp))\n")
        subprocess.run(["dune", "build", "--profile", "release", "-j", "2", "wp.cmxs"],
                       cwd=source, check=True)
        shutil.copy2(source / "_build/default/wp.cmxs", output / "wp.cmxs")
        shutil.copy2(source / "MemBytes.ml", output / "MemBytes.ml")
        shutil.copytree(source / "share", output / "share")
    receipt = {
        "spec_sha256": digest(SPEC), "plugin_sha256": digest(output / "wp.cmxs"),
        "share_sha256": {str(p.relative_to(output)): digest(p)
                         for p in sorted((output / "share").rglob("*")) if p.is_file()},
    }
    (output / "build.json").write_text(json.dumps(receipt, indent=2) + "\n")
    check(output)
    print("PASS: isolated corrected WP module built from pinned upstream source")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("build", "check", "run"))
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--archive", type=Path)
    args, rest = ap.parse_known_args()
    args.output = args.output.resolve()
    if args.action == "build":
        if rest:
            raise ValueError("unexpected build arguments")
        build(args.output, args.archive)
        return
    receipt = check(args.output)
    print("PHASE20_MODEL_SPEC_SHA256=" + receipt["spec_sha256"], flush=True)
    print("PHASE20_MODEL_PLUGIN_SHA256=" + receipt["plugin_sha256"], flush=True)
    if args.action == "run":
        if rest[:1] == ["--"]:
            rest = rest[1:]
        command = ["frama-c", "-no-autoload-plugins", "-load-plugin", "rtegen,server,region,eva",
                   "-load-library", "why3,qed,ocamlgraph", "-load-module", str(args.output / "wp.cmxs"),
                   "-wp-share", str(args.output / "share"), *rest]
        os.execvp(command[0], command)
    elif rest:
        raise ValueError("unexpected check arguments")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit("FAIL: Phase 20 model preparation: " + str(error))
