# Phase 20 toolchain reuse

This first OPT rollout reuses one previously executed corrected Frama-C/WP
build. It does not cache proofs, goal inventories, canary outcomes or evidence
acceptance. The actual Phase 20 targets, three semantic mutations, native
checks, original Phase 18/19 theorem replays and retained-evidence gates still
execute on every normal workflow run. Production C99, contracts, models and
the frozen v1 fixtures are unchanged.

## Independently pinned authority

`machine/formal/phase20-toolchain-reuse-v1.json` is reviewed source, outside the
cache. It identifies the immutable container, Linux AMD64 platform, complete
build inputs, reuse-policy inputs, successful main producer, archive digests
and every extracted file, including hidden share files. The build closure is
`phase20_model.py`, the correction specification and its patch. The specification
pins the official upstream source archive; the container pins OCaml, dune,
Frama-C, Why3 and Alt-Ergo. No mutable image tag or installed model is trusted
in place of those identities.

The initial artifact is from successful post-merge main run
[41381936801](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41381936801), attempt 1,
at commit `1bced8a1cf768a40a26d13eb0f33483a426f106f`:

| Identity | Approved value |
| --- | --- |
| Artifact | `13113896208`, `phase20-corrected-toolchain` |
| ZIP bytes | 2,570,664 |
| ZIP SHA-256 | `b494966dcc1fd4eacbc5a4e4d0698efc77d5145d33d2b9a528a85ac12090feea` |
| Tar SHA-256 | `e18d7ef08a5f3691b30865540e02412c4024cc21ac8d83a455447149c5eb77fc` |
| WP module SHA-256 | `bfd7e72b24af1a8d27c3a7df9de13c02c433c22a5af786bed02108c03a559f01` |
| Regular files / expanded bytes | 72 / 9,147,500 |

On an Actions cache miss, the helper checks repository, successful push/main
execution, exact commit/attempt/workflow, artifact ID, size and digest through
GitHub's API before downloading. It never forwards the API token to artifact
storage. A cache hit is checked against the same independent receipt, including
the complete payload manifest and the existing model checker. An internal
`build.json` cannot authorize its own payload. Extraction rejects aliases,
traversal, duplicates, nonregular members and bounded-size violations.

The exact cache key includes the entire receipt and current build/policy file
hashes. There are no prefix restore keys. Changed inputs cause a cold build;
missing or expired approved artifacts also fall back to cold. Corruption,
provenance mismatch and API permission/transport errors fail with a diagnostic
instead of being hidden by a fallback. Only a successful push to main may save
the already approved ZIP, after fresh model canaries. PRs do not publish caches.
Cold builds are not automatically admitted to the approved set.

The bounded ZIP is the only cached item (maximum 8 MiB compressed and 32 MiB
expanded). GitHub cache eviction is a safe miss. Cached approved bytes remain
usable after the original Actions artifact expires because the external
receipt still identifies those exact bytes. A future approved toolchain needs
a separately reviewed receipt; workflow execution never rewrites that authority.

## Fresh execution and historical evidence

Both preparation paths run the original inconsistency reproduction, corrected
false-claim rejection, seven copy/refutation controls, 48 affected library
subgoals, readonly controls and string-witness positive/negative lemma afresh.
The model is mounted read-only while canaries run, and results use a new output
directory. Only then is the same-run model artifact supplied to the existing
proof jobs. `preparation.json` distinguishes `COLD_BUILD_REQUIRED`,
`EXECUTED_FRESH` and `REUSED_VERIFIED_TOOLCHAIN`, and always records
`proof_results_reused: false`. Missing results cannot masquerade as completion.

The old v2 evidence and failed-execution logs remain byte-identical.
`phase20-replay-binding-v1.json` separately pins this CI orchestration and its
new dependencies. Its fixed exception set covers only the workflow and the
evidence validator's call to the new binding checker. Every original C,
contract, model, prover configuration, inventory and proof checker remains
bound to its old identity. This binding grants no new proof result and does
not relabel the historical failed workflow as successful. Current-head CI
must still execute all proofs and pass before merge.

## Measurement and rollback

The separate benchmark runs three cold builds and three reuse preparations,
alternating pair order on one Ubuntu 24.04 AMD64 runner. Every trial executes
fresh canaries and compares full semantic outcomes and goal inventories.
It records all six samples, preparation mode, model/input identities, checkout,
run/attempt, host metadata, image inspection, build/canary logs and medians.
Unknown versus timeout on a designated false claim both mean unproved;
positive obligations still require validity.

The predeclared promotion threshold is a 10% reduction in median **model
preparation plus fresh canary time**, with identical accepted outcomes and a
green normal Phase 20 proof workflow. Shared image-pull cost is recorded
separately. The first reuse trial includes approved-artifact download and
verification; later trials include local archive verification and extraction.
These trials do not measure Actions cache service latency, whole-workflow
elapsed time, other proof phases, or repeated full proof-suite performance.
The normal workflow's step timings provide a separate observation of cache
service transport. No speedup is claimed before the benchmark executes; the
PR must link the exact-head result artifact and all six samples.

Use the normal workflow's `workflow_dispatch` input `force_cold: true` for a
full cold build and all the same canaries and proofs. It bypasses cache restore,
archive download and cache publication. Local preparation supports the same
`--force-cold` switch. Removing/expiring the approved artifact causes cold
fallback on a cache miss; a cache integrity failure requires investigation or
an explicitly forced-cold run. Reverting this PR restores unconditional build
preparation and requires no production rollback.

The OPT plan uses complete effective-input identity, independent authority,
success-only publication, bounded storage and lifecycle measurements. The
reference plan was merged as private-context PR #6; OPT source revision is
`7556dd36acd53ed3ed538fd03b1db44e5c1ec869`. Proof-result reuse is a separate
future PR requiring full source/contract/model/dependency identities and
additional negative controls. Exact-head independent review remains required;
issue #28 and actual SHA-provider/canonical-JSON obligations remain open.
