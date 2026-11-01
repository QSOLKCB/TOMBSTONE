# P19-03 — Caller-memory composition and helper ownership

This is a new, conditional theorem over the unchanged production `equal32`,
`calculate_hash`, and `tb_receipt_verify_chain` bodies. It is not a replacement
for Phase 18's original 54-goal theorem. PR #27 merged at
`a548fdd0209fd199684f0446a636556597c6de8e`; its 19 post-merge workflows passed.
This follow-up starts at that commit and keeps issue #28 open.

## Memory contract

Let P be the explicitly modeled private provider effect and protocol state.
The helper may change its 32-byte output and P. All other pre-existing caller
memory must remain unchanged, including every byte of the receipt; on errors,
the output must also remain unchanged. Receipt and output are disjoint, as in
Phase 18. The chain may change P only: its complete receipt array, optional
trusted head, and all other memory outside P are preserved on success and
failure. The receipt array and trusted head may overlap each other.

The new ACSL frame expressly permits P; separation from caller inputs is an
explicit precondition. The successful-path genesis, predecessor flags, all
32-byte links and optional trusted-head equality postconditions are copied
verbatim from Phase 18, with the same arbitrary valid nonempty chain bound.
Explicit byte-preservation postconditions and cleanup are added. Projecting
away P gives the caller-visible no-write property. This does **not** prove
Phase 18's stronger literal global `assigns \nothing` / output-only frame.
In particular, freeing a context does not restore arbitrary allocator or
OpenSSL global state; the model never assumes that it does.

Within the modeled memory, the projection follows directly from the checked
frame: the helper's output is a fresh automatic array in the chain, and every
other permitted write is in P, disjoint from caller blocks. The chain proof
also checks explicit byte equalities for the complete receipt array and head.
Mapping the real provider heap, allocator metadata, thread-local state and
library globals into P is still an external refinement obligation. This is
not equivalence of timing, allocation counts or other provider APIs.

The original Phase 18 overlay, machine receipt, checker, and workflow remain
unchanged and run independently. The new composition cannot be substituted
for that historical theorem or used to mark its stronger helper frame closed.
The source, ABI, v1 fixture bytes and v0.1.0 are unchanged.

## Ownership and cleanup scope

`tools/phase19_bridge_overlay.py` introduces three proof-only state variables:
an unconstrained private effect byte, an owner token, and a protocol phase.
They represent effects and call history, not an actual allocated heap.

| Call | Required protocol | Assumed external transition |
| --- | --- | --- |
| `new` | No outstanding owner; phase 0 | Success yields a nonnull owned context, phase 1; error yields no owner |
| First/second `update` | Same owned context, phase 1/2 | Success advances the phase; error leaves cleanup required |
| `final` | Same context after two successful updates | Leaves cleanup required; an error preserves output |
| `free` | Same outstanding context, phase 1–4 | Consumes the owner token; phase returns to 0 |

WP checks the actual helper's call preconditions, error branches and empty
ownership postcondition. Missing cleanup must fail that postcondition; a
second free must fail the ownership precondition. Thus the proof concerns
the helper's use of the provider API, conditional on the external transition
contracts. Actual allocation freshness, allocator safety, backend storage
separation and real deallocation remain unproved refinement obligations.
The single-owner token describes this sequential helper invocation, not all
concurrent contexts or a new restriction on the production SHA API.

The [Frama-C/WP 32.1 manual](https://www.frama-c.com/download/frama-c-wp-manual.pdf),
section 1.6, documents the lack of implemented ACSL allocation/deallocation
clauses. We do not suppress unsupported allocation goals or label this token
model as a heap-lifetime proof.

## Shared assumptions and composition

Every target is generated from the **same** translation unit and contract set.
The chain uses exactly the helper specification checked in the helper job;
the equality body is checked separately under the explicit external `memcmp`
specification. `good_receipt` and `format_json` remain assumed production
helper contracts. Their implementation and canonical byte meaning are the
next independent obligations. The provider contract includes error statuses,
private effects, owner transitions and final-error output preservation.
Real SHA values, OpenSSL/HACL internals, compiler/runtime, external anchor
custody, historical events and physical erasure remain outside this theorem.

These contracts are consistent with inspected provider control flow, but code
inspection and finite fault tests do not discharge their universal premises.
No axiom says that the chain succeeds, that input receipts are already valid,
that the digest is correct, or that cleanup happens without calling `free`.

The executed Bytes model additionally emits **whole-block separation** premises:
the blocks containing `r`, `out`, the receipt array, trusted head, provider
context and update data are disjoint from the three private model variables
where those parameters occur. This is stronger than separating just the
specified byte ranges. It is part of this conditional theorem's assumption
boundary and still requires a real-provider refinement. Assigned owner/context
pointers have unspecified `from` dependencies; WP reports imprecision, not a
proved allocator relationship. External functions also use Frama-C's generated
exit/termination clauses. These are not new total-correctness claims.
The full emitted diagnostics are preserved and compared to
`machine/formal/phase19-bridge-diagnostics-v1.json`; an unexpected or changed
diagnostic fails CI. No warning-suppression flag is used.

## Evidence and acceptance

The new `phase19-bridge-wp.yml` runs three positive targets with Frama-C 32.1,
Bytes, Alt-Ergo and RTE, plus independently compiled semantic mutations for
caller corruption, missing cleanup and double cleanup. A timeout on an
unchanged positive target is failure. On a mutant, a timeout is evidence only
that the specified bad obligation was not proved, not a solver counterexample;
parser errors or missing goals are never accepted as semantic rejection.

The first execution at head `2fd2b5e3d00e8c6a17ee3dc2bbae8013d1c4804f`,
run `41353401932`, reported 11/11 equality, 51/51 hash, and 62/62 chain goals.
Missing cleanup left the cleanup postcondition unproved (47/48), duplicate
cleanup left free's two preconditions unproved (51/53), and caller corruption
left the caller-receipt postcondition and three safety/frame goals unproved
(51/55). The workflow **failed** because default WP output omitted individual
valid-goal records required by the new gate. This result is preserved, not
relabelled as green. The follow-up requests Frama-C's original JSON goal report.

The native control runner executes the unchanged 13-case helper harness and
requires a designated assertion failure from each compiled semantic mutant.
For caller corruption only, a test guard enables the write after fixture
parsing, so setup can complete before the caller-memory assertion is tested.
This guard is not in the positive source or formal mutant. GCC passed locally;
both GCC and Clang also passed in run `41353978018`.

That second run at head `dfcc419f8736d6095633e1d708d17519a72e623e`
checked out merge candidate `3394270823845a23de2930c0a6d5b0ea3f1d6b89`.
It reproduced all six solver results above and supplied full goal-by-goal
JSON. Its evidence gate still failed because the reader expected compact
JSON and Frama-C emitted multiline JSON. The corrected reader validates the
original retained reports locally, and fresh CI is required on its final head.
Both workflow failures remain recorded as failures.

`machine/formal/phase19-bridge-evidence-v1.json` binds that executed snapshot
to the actual source, headers, overlays, live provider test source, generated
proof hashes, raw job logs, model diagnostics and exact goal inventories.
The offline evidence gate rejects scope promotion, missing targets, changed
inputs/logs and relabelling a failed workflow. The unchanged original Phase 18
theorem separately passed 54/54 in run `41353978025`. These records describe
past executions, not final-head CI or independent review approval. See
[PR #29](https://github.com/QSOLKCB/TOMBSTONE/pull/29) for current checks.

Require fresh independent review of the final exact PR head and all current
CI before an owner merge. Review of #27 does not transfer. Keep issue #28 open
for remaining literal-frame/provider refinement obligations; do not tag or
release automatically. Next work: `good_receipt`/`format_json`, then actual
provider memory/lifetime and SHA refinement under the documented contract.
