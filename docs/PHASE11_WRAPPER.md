# Phase 11 — Whole-wrapper modular verification

**Scope:** the actual production `tb_witness_delete` function, including
`witness_header_status` (Phase 10), `splice_equal` (Phase 9),
`fingerprints` and the third SHA-256 call. It includes the unmodified
production `src/core/deletion.c` in a verification-only translation unit.

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
- `fingerprints`, the actual private helper, is **separately checked** against
  its own ACSL contract rather than automatically trusted.
- Frama-C runtime-error checks, missing/zero/incomplete proof goals and failing
  solver exits remain blockers.

## Boundary that is assumed, not proved

`tb_sha256_bytes` is given an explicit *external* ACSL contract. It guarantees
the digest buffer is writable/disjoint from input, restricts writes to 32
digest bytes and leaves those bytes unchanged on a provider error. It permits
`TB_OK`, `TB_ERR_CRYPTO` and `TB_ERR_MEMORY`. We do NOT establish its hash
algorithm's correctness, OpenSSL EVP semantics or absence of side channels.

If full-wrapper WP cannot discharge **every** nonzero obligation, the PR
remains a draft; record proof timeouts and proved/total counts. In particular,
a manually asserted helper contract is not enough unless that helper's own
proof is executed, reviewed and green.

Previous incomplete result: run 41307132302 (35/64, 29 timeouts). Phase 9
splice WP and Phase 10 prehash WP both passed on their exact source commits.

The published `v0.1.0` tag, canonical receipt wire format, public C ABI,
Rust clients, source archive and SHA-256 manifest remain untouched. No
automatic merge, release tag or blanket “formally verified” badge.
