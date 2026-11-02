#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import phase20_receipt_overlay as p

source = p.bridge.p18.SOURCE.read_text()
text = p.render()
assert p.strip(text) == source
for old, new in [(p.bridge.p19.GOOD,p.GOOD),(p.bridge.p19.FORMAT,p.FORMAT)]:
    assert old[:-3] in new
for unchanged in (p.bridge.HASH,p.bridge.CHAIN,p.bridge.LOOP):
    assert text.count(unchanged) == 1
for name, (_, old, new) in p.MUTANTS.items():
    altered = p.mutant(name)
    assert altered.replace(new,old,1) == text
    assert p.strip(altered) != source
for backend in p.HEX_BLOBS:
    assert p.render_hex(backend).count("tb_status tb_sha256_hex(") == 1
try:
    p.strip(text.replace(p.FORMAT,"",1))
except ValueError:
    pass
else:
    raise AssertionError("missing formatter contract accepted")
print("PASS: unchanged bodies, stronger original contracts, preserved chain theorem, distinct semantic mutants")
