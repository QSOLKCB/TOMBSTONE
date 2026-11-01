# Phase 20 — Actual receipt validation and formatter contracts

PR #29 merged at `f9140bdda31ea64f7e077115db6f0bb0622c7874` after clean
independent Codex review of exact head
`b13d1ba4e72ed697627c24e3cb90b62ff74eb8f8`. This follow-up targets the
`good_receipt` and `format_json` assumptions used by that caller-memory
composition. It preserves the production C99, headers, ABI, v1 fixtures,
original Phase 18 theorem, and all Phase 19 proof/evidence files.

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
remain distinguishable. Initial goal inventories are NOT_RUN, and the gate
fails until actual results and model diagnostics have been inspected and pinned.

Keep issue #28 and the broader A04/A05 obligations open. Require fresh
independent review of this PR's final exact head and all current CI. Review
of #29 does not transfer. No automatic merge, tag or release.

The next separate milestone is actual streaming SHA-provider refinement:
connect the private-state/owner abstraction to concrete allocation, backend
state, error transitions and cleanup, then address real digest semantics.
