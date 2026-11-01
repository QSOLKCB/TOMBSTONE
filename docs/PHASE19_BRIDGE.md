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
Phase 18's stronger literal global `assigns \\nothing` / output-only frame.
In particular, freeing a context does not restore arbitrary allocator or
OpenSSL global state; the model never assumes that it does.

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

## Evidence and acceptance

The new `phase19-bridge-wp.yml` runs three positive targets with Frama-C 32.1,
Bytes, Alt-Ergo and RTE, plus independently compiled semantic mutations for
caller corruption, missing cleanup and double cleanup. A timeout on an
unchanged positive target is failure. On a mutant, a timeout is evidence only
that the specified bad obligation was not proved, not a solver counterexample;
parser errors or missing goals are never accepted as semantic rejection.

At the initial implementation commit these new solver results are **NOT_RUN**.
Full original logs, exact PR/checkout identities and the final goal inventory
will be recorded after execution. Passing local generator/compilation tests
does not promote this status. All existing proof gates remain required.

Require fresh independent review of the final exact PR head and all current
CI before an owner merge. Review of #27 does not transfer. Keep issue #28 open
for remaining literal-frame/provider refinement obligations; do not tag or
release automatically. Next work: `good_receipt`/`format_json`, then actual
provider memory/lifetime and SHA refinement under the documented contract.
