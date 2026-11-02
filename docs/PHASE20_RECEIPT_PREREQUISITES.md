# Phase 20 — Actual receipt validation and formatter contracts

PR #29 merged at `f9140bdda31ea64f7e077115db6f0bb0622c7874` after clean
independent Codex review of exact head
`b13d1ba4e72ed697627c24e3cb90b62ff74eb8f8`. This follow-up targets the
`good_receipt` and `format_json` assumptions used by that caller-memory
composition. It preserves the production C99, headers, ABI, v1 fixtures,
original Phase 18 theorem, and all Phase 19 proof/evidence files.

**Acceptance is blocked by a reproduced inconsistency in the pinned Bytes
theory, as well as incomplete formatter obligations.** New regression checks
must not turn historical solver counts into trusted proof acceptance.

## Claims being checked

| Actual body | Contract |
| --- | --- |
| `zero32` | Pure Boolean result equivalent to all 32 bytes being zero |
| `equal32` | The unchanged Phase 19 byte-equality contract, under its existing libc premise |
| `good_evidence` | Pure Boolean result equivalent to the size bounds and the three evidence-kind cases |
| `good_receipt` | Its original pure Boolean contract plus exact receipt-validation equivalence |
| `tb_sha256_hex`, separately from both provider files | Valid disjoint input/output: OK, writes confined to 65 output bytes, terminal NUL at byte 64 |
| `hex32` | Actual wrapper, confined output and a readable terminated string |
| `format_json` | Original status/frame/successful-size contract, plus error-size preservation, successful NUL termination and unchanged receipt bytes |
| `calculate_hash` and chain | Re-execute the unchanged P19-03 contracts in the same environment as the newly checked bodies |

The formatter contract is about bounds, status and memory effects. It does
not specify exact canonical JSON contents, prove parser completeness, or
establish the receipt digest equation. The hex proofs establish framing and
termination, not the numeric meaning of every emitted hex digit. Native
golden-byte tests remain a distinct evidence class.

The native harness checks 160 validation cases and 2,530 formatter cases
(including 30 injected failures) per compiler/provider tuple on Ubuntu 24.04
x86-64. It now adds 324 cases with receipt, output and size in disjoint regions
of one allocation, including 180 injected failures. Both output/receipt orders,
three output offsets, four boundary capacities, all fixture/hash branches and
all observed fault sites are covered. Every byte outside the permitted output
and size regions must stay unchanged. These added cases passed locally with
GCC on both backends; current-head CI must independently execute all four
compiler/provider tuples. Its independent
Python oracle canonicalizes the frozen public toy fixtures and first checks
their recorded digests. It exercises every capacity from 1 through two bytes
past each expected output length, both `with_hash` branches, all observed
format-call sites, input preservation and both surrounding buffer guards.
Three compiled mutations must fail their designated semantic assertions.
Fault builds disable `snprintf` builtin folding and fortification so the
compiler cannot eliminate error branches before linker interposition. This
is a finite fault-test configuration, separate from normal production builds.

## External premises

The actual `snprintf` calls use four fixed literals and three argument shapes.
The proof-only preprocessor dispatch preserves every call argument and binds
them to explicit fixed-arity declarations. Their contracts require the exact
format bytes, readable NUL-terminated string arguments, writable bounded
destinations and separation. They assume confined writes and NUL termination
when the returned length fits. They do not assume that the caller's bounds
checks succeed or that the output is canonical. Unknown format strings,
`%n`, invalid string inputs and argument-shape substitutions are not covered.

The two five-byte `memcpy` calls in the formatter use an explicit readable,
writable, disjoint, byte-copy premise. `memcmp` retains Phase 19's premise.
These aliases are not libc implementations or proofs of libc internals.
Libc's real global/thread-local effects (including `errno`), implementation,
locale and source-to-machine refinement remain separate assumptions. In
particular, the abstract libc frame must not be advertised as a universal
no-global-effects guarantee for real `snprintf`.

The evidence retains every emitted model diagnostic, including the external
exit/termination defaults, pointer dependency warnings and whole-block
separation hypotheses. The hex-body proofs expose separation from their
private static digit table; the hash/chain proofs retain the Phase 19 private
state separation premises. These are conditional model results, not a proof
of arbitrary aliasing or real libc/provider state. Hex index bounds use WP's
built-in `wp:bitshift` proof strategy; no C operation is rewritten and no
bit-range axiom is added by this overlay.

The snprintf return/termination behavior follows the C interface described
in [WG14 N1548, 7.21.6.5](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1548.pdf).
The restricted frame is an explicit additional proof premise. Streaming SHA
ownership, allocation/lifetime, backend memory separation and actual digest
correctness remain open as documented in [Phase 19](PHASE19_BRIDGE.md).

## Source and evidence discipline

`tools/phase20_receipt_overlay.py` extends the Phase 19 shared translation unit
using registered comments, declarations and aliases. Stripping them restores
the byte-identical original receipt source. The two hex proof units extract
the exact function bodies from their separately pinned production provider
files; no reformatted or reimplemented loop is substituted.

Each actual target must pass Frama-C/WP 32.1, Bytes, Alt-Ergo and RTE with
nonzero complete goals and a complete original JSON goal report. Every
semantic mutant keeps the positive contracts: accept invalid receipts,
return an out-of-bounds success size, or modify the size on a formatter error.
It must leave the designated obligation unproved; a parser/tool failure does
not count as semantic rejection. Original successful and failed logs must
remain distinguishable. Execution is IN_PROGRESS: the retained validator,
hex and composition runs are complete, while the formatter remains partial.
The exact goal inventory and model diagnostics are now inspected and pinned
in `machine/formal/phase20-goals-v1.json`. The gate still fails until every
positive target is complete.

At [run 41364071336](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41364071336),
head `e8be500075ee00039a8edf88c013ad28ab9cb9a7` was tested through merge
checkout `8f159b36db6755744ebbc903d7fb7fd640b49baa`:

| Evidence | Executed result |
| --- | --- |
| Nine positive targets other than `format_json` | 289/289 WP/RTE goals |
| `format_json` | 132/139; incomplete |
| Accept-invalid mutant | 7/8; designated equivalence goal unproved, native mutant rejected |
| Bad-size and error-size mutants | 131/139 and 132/140; formal acceptance blocked by the incomplete positive formatter |
| Native GCC/Clang × OpenSSL/HACL | All four jobs passed the 160 validation / 2,530 formatting cases and all three semantic controls |

The seven open formatter goals concern three intermediate string assertions,
the final call's separation requirement, an intermediate receipt-frame
assertion, final receipt preservation and successful NUL termination. Their
exact identifiers and original reports are retained; a proved top-level goal
cannot discharge unproved supporting assertions. This is a proof-completion
blocker, not an observed runtime failure.

The next proof iteration split the intermediate string conjunctions into
individually checked assertions and adds checked byte-separation, length and
NUL witnesses at the actual statement boundaries. These are additional WP
obligations, not assumptions. It leaves every original function precondition,
postcondition, external libc premise and production C statement unchanged.
The retained 132/139 snapshot cannot certify a changed overlay; its source
identity gate must reject it until fresh execution is recorded.

At [run 41367373120](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41367373120),
head `30e7a7df4c37950618b5826a2ab137924560f6bf` reported 158/182 formatter
goals, 156/182 bad-size and 158/183 error-size. All 24 open positive goals
are retained in the original logs; new checked assertions are obligations,
not free assumptions. Composition still reported 51/51 and 62/62, but its
inventory gate rejected source-line movement in otherwise identical warning
text. A regression replays both original composition reports and now
normalizes only line numbers in the six exact generated Phase 20 filenames.
Filenames, warning text, goal IDs/counts and verdicts remain significant.
This does not refresh any source identity or certify a changed overlay.

The five red jobs in that run were the formatter, its two mutants, stale
retained evidence and the diagnostic-location mismatch. The shared
`NOT_YET_RECORDED` failure did not recur. There are 25 new focused diagnostic
regression checks, run before evidence inspection so stale evidence cannot
prevent the regressions from executing.

## Byte-memory-model blocker

`tests/formal/phase20_bytes_model_canary.mlw` imports the installed, unchanged
Frama-C 32.1 `MemBytes` theory. It creates two memory states whose byte at
offset 1 is respectively 17 and 34, then copies one byte at offset 0. That
copy must preserve the destination's byte at offset 1. The theory's copy
definition starts its update from the source block, while its separation
lemma promises preservation from the destination block. Alt-Ergo 2.5.4
accepts both resulting values and their conjunction. This is an executed
contradiction in the imported theory, not an observed defect in TOMBSTONE's
production C or a generic claim that solver timeouts imply unsoundness.

The model SHA-256 is
`16478d1b77f282539b642b174bbf8225a5d30fe0442e5e1cd46ada8e1f05c61a`.
The same bytes occur in the pinned image and the
[official Frama-C 32.1 source archive](https://www.frama-c.com/download/frama-c-32.1-Germanium.tar.gz).
Local original solver outputs and machine results are retained in
`formal/evidence/phase20/bytes-model-canary-local/` and
`machine/formal/phase20-model-blocker-v1.json`. The local run used the exact
image's Why3 1.8.2 and Alt-Ergo 2.5.4 binaries, exporting tasks before running
Alt-Ergo directly. It did not substitute a hand-written memory implementation.

The CI evidence job runs the same canary inside the digest-pinned image and
retains its exported tasks and raw outputs. Four positive controls must pass;
neither false byte-copy claim may be proved. A version/model mismatch, missing
task, solver error or inconclusive control blocks the check. A passing canary
would only exclude this specific contradiction, not prove model soundness.
The current model is expected to fail explicitly. Do not patch the theory
silently, drop its frame conditions or promote the other solver results.

Next: independently assess the model definition/lemma mismatch and the
Phase 18/19 dependency; choose and review a corrected pinned toolchain or an
explicit model refinement; rerun this canary and all affected positive and
negative proofs; then finish the formatter, refresh evidence and obtain fresh
exact-head independent review. Actual SHA-provider refinement follows that
gate. Issue #28 stays open.

WP's summary includes automatic termination/unreachable CFG facts that its
JSON report omits. The gate accounts for those separately and requires every
scheduled goal to appear exactly once in the original structured report.
An automatic CFG fact cannot substitute for a missing scheduled obligation.

Formatter runs export actual string-literal bytes with `-wp-literals` and
use checked intermediate frame/string assertions. `-wp-no-callee-precond`
removes redundant post-call precondition hypotheses; the call-site
precondition obligations are still generated and must all pass. A literal
byte assertion catches the default zero-string abstraction. The failed Z3
experiment is retained as history, not an accepted prover dependency.
The four finite format comparisons are expanded byte by byte, including
the NUL. `sizeof` guards reject a different `PRIu64` expansion from this
64-bit proof model instead of silently interpreting it as the recorded format.

`check_phase20_evidence.py --inspect-incomplete` may validate the integrity
of an explicitly incomplete snapshot; it prints `INCOMPLETE`, not proof
acceptance. The default evidence command and individual positive WP gates
reject every incomplete target. Formatter mutation results cannot count as
accepted formal negative controls while their positive baseline is partial.
Historical execution identities and current replay/validation dependencies
are recorded separately from final-head CI and independent review. A
consistent retained snapshot cannot grant current-head acceptance.

Keep issue #28 and the broader A04/A05 obligations open. Require fresh
independent review of this PR's final exact head and all current CI. Review
of #29 does not transfer. No automatic merge, tag or release.

The next separate milestone is actual streaming SHA-provider refinement:
connect the private-state/owner abstraction to concrete allocation, backend
state, error transitions and cleanup, then address real digest semantics.
