#!/usr/bin/env python3
"""Phase 18 WP log checker rejects fake, vacuous or incomplete proof evidence."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from check_phase18_wp_log import validate
samples={
 "missing":"[wp] Running WP plugin\n",
 "vacuous":"[wp] Function tb_receipt_verify_chain\n[wp] Proved goals: 0 / 0",
 "partial":"[wp] Function tb_receipt_verify_chain\n[wp] Proved goals: 12 / 13",
 "wrong_function":"[wp] Function other_function\n[wp] Proved goals: 13 / 13",
 "timeout":"[wp] Function tb_receipt_verify_chain\n[wp] Timeout on goal\n[wp] Proved goals: 13 / 13",
 "duplicated":"[wp] Function tb_receipt_verify_chain\n[wp] Proved goals: 13 / 13\n[wp] Proved goals: 13 / 13",
}
for name,text in samples.items():
    try: validate(text)
    except ValueError: continue
    raise AssertionError("invalid WP result accepted: "+name)
assert validate("[wp] Function tb_receipt_verify_chain\n[wp] Proved goals: 13 / 13")==13
print("PASS: Phase 18 missing, vacuous, partial, irrelevant, timeout and duplicate WP logs rejected")
