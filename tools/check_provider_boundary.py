#!/usr/bin/env python3
"""Source-pinned Phase 12 claim-scope check (NOT a cryptographic proof)."""
import json
import pathlib
import subprocess
root=pathlib.Path(__file__).resolve().parent.parent
r=json.loads((root/"machine/formal/phase12-provider-boundary-v1.json").read_text())
assert r["format"]=="tombstone.proof-boundary" and r["phase"]==12
assert r["release_unchanged"]=="v0.1.0"
p=root/r["production_path"]
actual=subprocess.check_output(["git","hash-object",str(p)],cwd=root,text=True).strip()
assert actual==r["production_git_blob_sha"], "provider source changed without updated evidence"
assert (root/r["test_path"]).is_file()
assert "OpenSSL EVP formally verified" in r["explicit_nonclaims"]
assert "SHA-256 mathematically verified for all input" in r["explicit_nonclaims"]
print("PASS: production C99 source identity and Phase 12 explicit nonclaims retained")
