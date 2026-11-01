#!/usr/bin/env python3
"""Source fidelity, theorem preservation, and adversarial evidence gate tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import phase19_bridge_overlay as overlay
import check_phase19_bridge_log as gate


def reject(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError("invalid evidence accepted")


source = overlay.p18.SOURCE.read_text()
rendered = overlay.render()
assert overlay.strip(rendered) == source
# All four old successful-path postconditions are copied, not rephrased or weakened.
old = overlay.p18.ANNOTATIONS[overlay.CHAIN_MARKER]
assert old[old.index("  ensures"):old.index("*/")] in overlay.CHAIN
assert "  assigns \\nothing;" in old
assert "  assigns out[0 .. 31];" in overlay.p18.ANNOTATIONS[overlay.p19.HASH_MARKER]
assert overlay.ANNOTATIONS[next(iter(overlay.p18.ANNOTATIONS))] == next(iter(overlay.p18.ANNOTATIONS.values()))
for name, (before, after) in overlay.MUTANTS.items():
    altered = overlay.mutant(name)
    assert altered.replace(after, before, 1) == rendered
    assert overlay.strip(altered) != source
reject(lambda: overlay.strip(rendered.replace(overlay.HASH, "", 1)))


def report(target):
    ids = ["bytes_" + target + "_" + suffix for suffix in gate.REQUIRED[target]]
    text = "32.1 (Germanium)\n[rte:annot] annotating function " + target + "\n"
    text += f"[wp] {len(ids)} goals scheduled\n"
    text += "".join(f"[wp] [Qed] {goal} : Valid (1ms)\n" for goal in ids)
    text += f"[wp] Proved goals: {len(ids)} / {len(ids)}\n"
    return text, ids


for target in gate.TARGETS:
    good, ids = report(target)
    gate.validate(good, target, inventory={target: sorted(ids)})
    bad = ["", good + good, good.replace("32.1", "33.0"),
           good.replace("[rte:annot]", "[skipped]"),
           good.replace(ids[-1], ids[0]),
           good.replace("[Qed]", "[Timeout]", 1),
           good + "[wp:warning] unsupported allocation\n",
           good.replace(" : Valid", " : Unknown", 1)]
    for text in bad:
        reject(lambda: gate.validate(text, target))
    reject(lambda: gate.validate(good, target, inventory={target: []}))

good, _ = report("calculate_hash")
for mutant, goal in [("missing-cleanup", "ensures_cleanup"),
                     ("caller-corruption", "ensures_caller_receipt")]:
    bad = good.replace(f"[Qed] bytes_calculate_hash_{goal} : Valid (1ms)",
                       f"[Timeout] bytes_calculate_hash_{goal} (10s)")
    bad = bad.replace("Proved goals: 3 / 3", "Proved goals: 2 / 3")
    gate.validate(bad, "calculate_hash", mutant)
    reject(lambda: gate.validate(good, "calculate_hash", mutant))
    reject(lambda: gate.validate(bad + "[kernel:abort] syntax error", "calculate_hash", mutant))
print("PASS: exact source, original theorem preservation, semantic mutant construction, adversarial WP log rejection")
