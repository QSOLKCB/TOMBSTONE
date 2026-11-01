# Phase 10 — Public C99 witnessed-deletion wrapper (under review)

**Target:** the actual production function `tb_witness_delete`, not a
reimplementation of its algorithm. Phase 9's `splice_equal` was proved
with Frama-C/WP for arbitrary valid lengths; Phase 10 attempts the public
wrapper's argument/length/mismatch/result/output contract.

## Scope and assumptions

`formal/framac/witness_wrapper.c` declares additional ACSL contracts and
then **includes** the original `src/core/deletion.c` for source-level WP.
The proof harness introduces no production SHA-256 implementation and never
modifies the C ABI.

The separately declared `tb_sha256_bytes` contract is **assumed**. It permits
success or a provider memory/crypto failure, assumes valid and disjoint
buffers, limits writes to digest output, and requires no digest changes
on failure. **Frama-C does not verify OpenSSL or actual SHA-256** in this
phase. The actual provider needs its own proof to close this assumption.

The caller must supply real valid readable objects when required and a valid
non-overlapping writable output object. Invalid non-null pointers cannot
be made safe by numeric length checking alone.

## Intended obligations

- Output remains byte-for-byte unchanged on any error return.
- Success implies explicit deletion classification, exact byte lengths and
  exact caller-supplied offset.
- Error precedence: argument before length before mismatch before hashes.
- Hash failure never causes the public output to be written.
- Frama-C/WP runtime safety obligations (RTE) are enabled.

**Status:** unproved until the exact-head CI reports all nonzero goals
discharged. Missing, partial and zero-goal summaries fail CI.

**Not proved here:** SHA-256/OpenSSL implementation, Rust bindings,
compiler/ABI equivalence, receipt chain or real historical deletion events.

The released `v0.1.0` tag and its checksummed source remain unchanged.
