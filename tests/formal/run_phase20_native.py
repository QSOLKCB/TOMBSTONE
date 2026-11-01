#!/usr/bin/env python3
"""Compile actual source, then require designated native mutant failures."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import phase20_receipt_overlay as p
from check_portability import canonical, independent_digest, FIXTURES

def run(args,**kwargs):
    return subprocess.run(args,cwd=ROOT,text=True,check=True,**kwargs)

ap=argparse.ArgumentParser()
ap.add_argument("--cc",default=os.environ.get("CC","cc"))
ap.add_argument("--backend",choices=("openssl","hacl"),default="openssl")
args=ap.parse_args()
build=ROOT/"build"/("phase20-"+args.backend+"-"+Path(args.cc).name)
run(["make","all","CC="+args.cc,"SHA256_BACKEND="+args.backend,"BUILD_DIR="+str(build)])
with tempfile.TemporaryDirectory(prefix="phase20-") as temporary:
    directory=Path(temporary)
    oracle=[]
    for name in FIXTURES:
        receipt=json.loads((ROOT/"machine/examples"/name).read_bytes())
        assert independent_digest(receipt) == receipt["receipt_hash"]
        path=directory/name; path.write_bytes(canonical(receipt)); oracle.append(str(path))
    common=[args.cc,"-std=c99","-O2","-fno-builtin-snprintf","-U_FORTIFY_SOURCE","-D_FORTIFY_SOURCE=0","-Wall","-Wextra","-Wpedantic","-Werror","-Iinclude",
            "tests/formal/test_phase20_native.c",str(build/"libtombstone.a"),
            "-Wl,--wrap=snprintf","-Wl,--wrap=__snprintf_chk"]
    if args.backend == "openssl": common.append("-lcrypto")
    executable=directory/"native"
    run(common+["-o",str(executable)])
    run([str(executable),*oracle])
    source=p.bridge.p18.SOURCE.read_text()
    expected={"accept-invalid":"VALIDATION_REJECT","bad-size":"FORMAT_SIZE","error-size":"ERROR_SIZE"}
    for name,(_,old,new) in p.MUTANTS.items():
        if name == "accept-invalid":
            replacement=new.replace("return 1;","if (p20_mutation_active) return 1;",1)
        elif name == "bad-size":
            replacement="    if (p20_mutation_active) { *size = capacity; } else { *size = (size_t)k; }"
        else:
            replacement=new.replace("*size = 0;","if (p20_mutation_active) *size = 0;",1)
        assert source.count(old) == 1
        path=directory/(name+".c"); path.write_text(source.replace(old,replacement,1))
        run(common+[f'-DP20_SOURCE="{path}"',"-o",str(executable)])
        result=subprocess.run([str(executable),*oracle],cwd=ROOT,text=True,capture_output=True)
        if result.returncode != 1 or f"FAIL[{expected[name]}]" not in result.stderr:
            raise SystemExit(f"FAIL: {name}: expected {expected[name]}, observed {result.returncode}: {result.stderr}")
        print(f"PASS: native {name} rejected specifically by {expected[name]}",flush=True)
