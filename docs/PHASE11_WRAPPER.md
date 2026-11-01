# Phase 11 — Whole-wrapper modular verification

**Scope:** the actual production `tb_witness_delete` function, including
`witness_header_status` (Phase 10), `splice_equal` (Phase 9),
`fingerprints`, the new production `witness_stage` helper, and the third
SHA-256 call. It includes the actual development `src/core/deletion.c` in
a verification-only translation unit. Phase 11 refactors the local evidence
construction into the private production `witness_stage` helper; no public
ABI or receipt-format change is intended.

## Executed Phase 11 proof — 88/88

**Verified source:** `src/core/deletion.c` Git blob `a3dce4e7a78b591028d33c230c2b417f12945729`, source commit `53a31739496788a2e1c7b195339b4e8648999e7d`. The proof-only overlay is `formal/framac/witness_wrapper_v11.c` blob `bddf6ef44cd97f65a052a47860a09909a4d71e7c`.

[Executed GitHub Actions run 41314458282](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41314458282), using Frama-C 32.1 and Alt-Ergo 2.5.4 under a pinned Docker image digest, proved **88/88** nonzero goals:

| Actual C99 function | WP goals | Memory model |
| --- | --- | --- |
| `fingerprints` | **18/18** | default typed model |
| `witness_stage` | **23/23** | Bytes |
| `tb_witness_delete` | **47/47** | Bytes |

All three use `-wp-rte` and the fail-closed goal checker. The exact workflow uploaded three separate proof logs in the `tombstone-phase11-modular-wp-logs` artifact (ZIP digest `sha256:1b186c39037f95a59f4dd9d56f4bf5a990b1e8e703611de76717d82623ed6a1e`). The original C99/Rust/GTK/CBMC/fuzz/Phase 9/Phase 10/documentation/source-candidate workflows also passed on this commit.

**Scope:** This is a modular *source-level* proof of the specified witness properties under valid pointer/object requirements, defined C memory models, and the explicitly **assumed external SHA-256 function contract**. It does not verify OpenSSL EVP, the SHA-256 digest algorithm, binary compilation, the OS, hardware or real historical deletion. Independent exact-head review and merge remain outstanding.

**Machine-readable provenance:** `machine/formal/phase11-wp-evidence-v1.json` pins source/overlay Git blob IDs and proof provenance. CI checks these identities; the JSON is not itself a signed attestation.

The goal is a complete, modular source-level contract for every documented
argument, length, mismatch, successful metadata and no-write-on-error case,
including every SHA provider failure. This is more than the 25-goal prehash
proof, and does not substitute one for the other.

## Non-negotiable proof obligations

- Exact splice relationship is necessary for success and for any hash-provider
  execution; a false explicit-delete cannot pass the specification.
- Argument/length/mismatch status precedence agrees with the public ABI.
- Successful output records exact sizes, caller offset and explicit kind.
- Failed calls do not mutate the caller-owned output, including padding bytes
  insofar as the C memory model and ACSL specification permit.
- Both `fingerprints` and `witness_stage` are actual private production helpers;
  each is **separately checked** against its own ACSL contract rather than
  being automatically trusted.
- Frama-C runtime-error checks, missing/zero/incomplete proof goals and failing
  solver exits remain blockers.

## Boundary that is assumed, not proved

`tb_sha256_bytes` is given an explicit *external* ACSL contract. It guarantees
the digest buffer is writable/disjoint from input, restricts writes to 32
digest bytes and leaves those bytes unchanged on a provider error. It permits
`TB_OK`, `TB_ERR_CRYPTO` and `TB_ERR_MEMORY`. We do NOT establish its hash
algorithm's correctness, OpenSSL EVP semantics or absence of side channels.

A future change must discharge **every** nonzero obligation again on its exact source. If any proof target fails, the PR is blocked; retain failure evidence and proved/total counts. In particular,
a manually asserted helper contract is not enough unless that helper's own
proof is executed, reviewed and green.

Previous incomplete result: run 41307132302 (35/64, 29 timeouts). Phase 9
splice WP and Phase 10 prehash WP both passed on their exact source commits.

The published `v0.1.0` tag, canonical receipt wire format, public C ABI,
Rust clients, source archive and SHA-256 manifest remain untouched. No
automatic merge, release tag or blanket “formally verified” badge.

## Executed negative evidence

- Phase 11 first run [41311888973](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41311888973): `fingerprints` 14/18; four timed-out memory preconditions; wrapper not executed.
- Second run [41312320907](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41312320907): `fingerprints` 18/18, whole wrapper **49/61** with twelve timed-out properties (memory framing and helper call preconditions). The successful helper did **not** certify the wrapper.
- Subsequent staging attempts proved 36/39, 38/39, and 39/43 obligations; changing to the byte-oriented memory model and moving metadata assignment into the public wrapper resolved the remaining obligations. The final source and three-stage proof passed **18/18, 23/23, 47/47** in run 41314458282.
