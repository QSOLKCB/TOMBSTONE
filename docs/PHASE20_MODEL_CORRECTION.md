# Phase 20 byte-memory correction

The original pinned Frama-C 32.1 Bytes theory proved both 17 and 34 for the
same untouched byte. The canary correctly blocked acceptance. The original
head `997695ac1feb13df39d50d599f9ca7a25dca8fb8` and all twelve job logs from
run `41370482031` remain recorded as failed attempt 17.

This change supplies an explicit local correction to upstream WP, rather
than treating the original inconsistent model as proof evidence. It is a
candidate requiring independent review, not an upstream-endorsed fix or a
general toolchain soundness proof.

## Exact changes

`machine/formal/phase20-model-correction-v1.json` pins the official 32.1
source archive, the patch, and all four original and corrected files.
`tools/phase20_model.py` checks those identities, builds only WP against the
installed pinned kernel, and loads it explicitly. The original installation
and historical Phase 18/19 records are preserved. The correction adds no
axiom and does not change any library lemma statement.

* `memcpy` must start with the destination block, preserving bytes outside
  the copied interval. The upstream definition started with the source
  block, contradicting its copy-separation lemmas.
* `to_seq` takes an end offset. The copied source interval must end at
  `source.offset + size`. The same correction is made in both byte orders,
  their separation-lemma proof hints, and the theory generator.
* Readonly global objects, including lifted literals, receive negative
  bases under the model's existing readonly-address convention. The former
  positive bases made lifted literals appear writable. Mutable globals
  retain positive bases; local-object handling is unchanged.

The patch applies to upstream LGPL-2.1 WP source; its upstream copyright
and licensing remain in force. TOMBSTONE's Apache-2.0 license is unchanged.
The original source URL and the complete modification are retained so the
isolated module can be rebuilt.

## Required regression evidence

The CI model job must reproduce the old contradiction as a negative control,
then reject both false claims under the corrected model. Every positive
control must prove. Separate positive goals prove the negations of the two
false claims; a negative timeout alone is not the correction's evidence.
Seven additional goals cover nonzero source/destination offsets, destination
neighbours, and the equivalence of signed/unsigned character copy views.
All 48 affected copy-separation subgoals across both byte orders must prove.
An actual-C readonly probe checks globals, lifted literals and mutable data;
its writable-literal mutant must fail its designated assertion.

The formatter keeps its original caller preconditions and guarantees.
Checked ghost lengths preserve terminator witnesses through calls. The
signed-char memcpy postcondition is the view equivalence checked above;
libc implementation correctness remains an external premise. Branch
splitting decomposes proof obligations without removing any path or RTE
check. Its expanded goal inventory must be recorded from actual CI output.

All Phase 20 targets and semantic mutants must rerun with the corrected
module. A separate compatibility job replays the unchanged original Phase
18 chain theorem and Phase 19 equality/hash/error contracts. Their old
successful runs do not substitute for this replay.

## Execution status before CI renewal

Executed locally: reproducible isolated WP build; original contradiction;
corrected positive controls and rejection of both false claims; all seven
copy/refutation goals; all 48 library subgoals; readonly positive checks;
eight model-gate tests; 25 diagnostic regressions; exact-source overlay
integrity. Local WP tasks were exported through the normal Why3 driver and
executed directly with the pinned Alt-Ergo because the local host cannot
run Why3's socket server. Export-only WP reports are not accepted as CI
proof receipts.

Full formatter, semantic mutants, compatibility replay and fresh exact-head
CI evidence are still pending. The retained historical proof snapshot stays
blocked until actual complete reports and their identities are recorded.
Issue #28 and the independent review gate remain open. No merge, tag or
release is authorized by these tests.
