#!/usr/bin/env python3
"""Phase 19 source fidelity and nonvacuity negative controls."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(name,file):
    sp=importlib.util.spec_from_file_location(name,ROOT/"tools"/file)
    mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod);return mod
m=load("equal_overlay","phase19_equal32_overlay.py")
p=load("phase18_overlay","phase18_wp_overlay.py")
src=p.SOURCE.read_bytes().decode()
out=m.render()
assert out.count("static int equal32(const unsigned char *a, const unsigned char *b)")==1
assert out.count("extern int memcmp(")==1
assert "ensures \\result == 1 <==>" in out
assert "ensures \\result == 0 <==>" in out
assert "assigns \\nothing;" in out
assert out.replace(m.EXT,"",1).replace(p.ANNOTATIONS["static int equal32(const unsigned char *a, const unsigned char *b)"],"",1)!=src
stripped=out.replace(m.EXT,"",1)
for annotation in p.ANNOTATIONS.values():
    stripped=stripped.replace(annotation,"",1)
assert stripped==src
try:
    p.render(src.replace("static int equal32", "static int fake32",1))
except ValueError:pass
else:raise AssertionError("mutated actual implementation source accepted")
print("PASS: actual equal32 proof is source-identical with explicit unproved libc boundary")
