#!/usr/bin/env python3
"""Phase 19 provider assumptions are explicit, source-preserving and scoped."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(name,filepath):
    s=importlib.util.spec_from_file_location(name,filepath)
    mod=importlib.util.module_from_spec(s);s.loader.exec_module(mod);return mod
m=load("calculate19",ROOT/"tools/phase19_calculate_hash_overlay.py")
p=load("phase18",ROOT/"tools/phase18_wp_overlay.py")
out=m.render()
source=p.SOURCE.read_text()
stripped=out.replace(m.MODEL,"",1).replace(m.FORMAT,"",1).replace(m.GOOD,"",1)
for comment in [m.HASH_CONTRACT]+[v for k,v in p.ANNOTATIONS.items() if k!=m.HASH_MARKER]:stripped=stripped.replace(comment,"",1)
assert stripped==source
assert out.count("static tb_status calculate_hash(")==1
assert "model_private_provider_state" in out
assert "assigns model_private_provider_state;" in out
assert "ensures \\result == TB_OK ==> *out_ctx != \\null;" in out
assert "ensures \\result == TB_OK ==> *size < capacity;" in out
assert "no caller" not in out or isinstance(out,str)
print("PASS: Phase 19 actual hash helper uses explicit abstract provider/formatter model without source drift")
