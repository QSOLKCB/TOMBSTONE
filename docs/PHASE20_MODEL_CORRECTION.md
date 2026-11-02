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
Checked ghost lengths preserve terminator witnesses through calls. A pure,
empty ghost helper proves the elementary implication from a bounded readable
NUL witness to `p20_cstr`. CI proves that exact helper separately and rejects
its missing-NUL-premise mutant; its contract is not an external assumption.
Every call-site precondition remains a formatter proof obligation. The
signed-char memcpy postcondition is the view equivalence checked above;
libc implementation correctness remains an external premise. Branch
splitting decomposes proof obligations without removing any path or RTE
check. Its expanded goal inventory must be recorded from actual CI output.

All Phase 20 targets and semantic mutants must rerun with the corrected
module. A separate compatibility job replays the unchanged original Phase
18 chain theorem and Phase 19 equality/hash/error contracts. Their old
successful runs do not substitute for this replay.

## Executed correction and replay

Executed locally: reproducible isolated WP build; original contradiction;
corrected positive controls and rejection of both false claims; all seven
copy/refutation goals; all 48 library subgoals; readonly positive checks;
nine model-gate tests (including omitted/changed artifact files); 25 diagnostic regressions; exact-source overlay
integrity. Local WP tasks were exported through the normal Why3 driver and
executed directly with the pinned Alt-Ergo because the local host cannot
run Why3's socket server. Export-only WP reports are not accepted as CI
proof receipts.

Run `41375387461` independently passed the corrected-model regressions and
all four native compiler/provider tuples. Its downstream proof jobs rejected
the model artifact before execution: upload omitted exactly `share/.gitignore`,
`share/why3/.gitattributes` and `share/why3/.gitignore`. The downloaded ZIP
matches GitHub's artifact digest, and all present share files match the build
manifest. Attempt 18 and all fourteen original logs preserve that failure.
Toolchain transport now uses a tar archive; the integrity checker still
requires the complete manifest. The string-witness helper proved locally,
its missing-premise mutation did not prove, and all 30 selected string
assertion subgoals reduced to Qed with the proved helper.

Run `41376577333`, head `1117798e0de9e8122344dfb4882dd6a4056cffea`, then
passed the corrected-model and ghost-lemma checks, all four native tuples,
1,392/1,392 positive WP/RTE obligations, and the unchanged original theorem
replays (54/54, 11/11, 40/40, 41/41). The formatter accounts for 1,103 of those
positive obligations. Its bad-size mutant leaves only eight size-bound and
eight termination obligations unproved; its error-size mutant leaves only
the two size-on-error obligations unproved. Accept-invalid retains its
designated receipt-equivalence failure.

The workflow still failed its old evidence/inventory gates. The v2 evidence
records that failure honestly and preserves all fourteen original logs and
105 original model-result/log files. It binds every target to the same
recorded model build and validates the original canary, library, readonly,
ghost-lemma and compatibility reports. A new CI run validates the current
build identity independently; historical binary hashes are not substituted
for the current run's artifact.

The old v1 evidence and inventories remain unchanged. Local acceptance and
117 adversarial evidence rejections pass, including dependency-name errors,
wrong model identities, altered canaries and missing theorem replays. Final
exact-head CI and independent review are still required. Issue #28 remains
open. No merge, tag or release is authorized by these tests.
