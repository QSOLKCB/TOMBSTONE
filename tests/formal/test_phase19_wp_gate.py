#!/usr/bin/env python3
"""Reject plausible-looking reports for the wrong or incomplete proof."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from check_phase19_wp_log import EXPECTED, FUNCTION, validate

for target, count in EXPECTED.items():
    function = FUNCTION[target]
    good = (f"32.1 (Germanium)\n[rte:annot] annotating function {function}\n"
            f"[wp] {count} goals scheduled\n[wp] Proved goals: {count} / {count}\n")
    assert validate(good, target) == count
    bad = {
        "empty": "",
        "name only in command": f"frama-c -wp-fct {target}\n[wp] Proved goals: {count} / {count}\n",
        "wrong RTE function": good.replace("annotating function " + function, "annotating function unrelated"),
        "no RTE": good.replace("[rte:annot]", "[comment]"),
        "wrong version": good.replace("32.1", "33.0"),
        "zero": good.replace(str(count), "0"),
        "partial": good.replace(f"{count} / {count}", f"{count-1} / {count}"),
        "fewer obligations": good.replace(str(count), str(count-1)),
        "duplicated": good + good,
        "earlier failure": good.replace(f"{count} / {count}", f"{count-1} / {count}") + good,
        "timeout": good + "[wp] Timeout\n",
        "unknown": good + "[wp] Goal x : Unknown\n",
        "unsupported": good + "[wp] Warning: unsupported predicate\n",
        "missing RTE guards": good + "[wp] Warning: Missing RTE guards\n",
        "error": good + "[kernel:annot-error] invalid contract\n",
    }
    for label, log in bad.items():
        try:
            validate(log, target)
        except ValueError:
            continue
        raise AssertionError(f"accepted {target}: {label}")
print("PASS: 45 missing, stale, partial, wrong-target and warning/error reports rejected")
