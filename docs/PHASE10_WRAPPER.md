# Phase 10 — Public witnessed-deletion validation proof

**Implementation status: in PR, exact-head Frama-C/WP gate.**

The actual production `tb_witness_delete` now calls a small static
`witness_header_status` helper that checks **all prehash public-API errors**
in the same order as v0.1.0: argument error, invalid size/offset error,
then incompatible after-length error. This helper does not inspect caller
byte values, write to caller memory, allocate or perform cryptography.

Its ACSL contract describes the return-status domain, the *if and only if*
argument-error condition, the necessary length/mismatch conditions and
the exact successful length/offset invariants. The proof runs against the
production `src/core/deletion.c` function with arbitrary `size_t` inputs.
The `assigns \nothing` contract forbids any caller-visible mutation.

**Separate executable fault test:** `tests/formal/test_wrapper_hash_failures.c`
includes the real production C99 wrapper and uses a *test-only* SHA provider
stub that fails at the first, second and third hash calls. It validates
success metadata, error precedence, early rejection before hashing and that
failures never modify caller output. This is an executed regression test,
**not** an unbounded proof of those full-wrapper outcomes.

## Complete wrapper proof remains open

The exploratory `formal/framac/witness_wrapper.c` still states the
**intended complete** `tb_witness_delete` contract and an explicitly assumed
external `tb_sha256_bytes` contract. Initial Frama-C run
[41307132302](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41307132302)
discharged **35/64** goals, with 29 timeouts. It is **not a proof**.
It is excluded from the release claim and not silently counted as passed.
Its remaining work includes pointer casts and memory modeling, call-site
preconditions, struct-output framing, and hash-provider assumptions.

## Independent proof gate

CI `.github/workflows/formal-wrapper.yml` must prove all generated,
nonzero goals for the production helper with `-wp-rte`, preserve the
Frama-C log, and run the native failure regression. It fails closed on
incomplete results. Phase 9's 35/35 proven splice relation is preserved.

**Not proved:** the entire public witness wrapper, actual OpenSSL/SHA-256,
output preservation for all abstract hash failures, Rust, compiled machine
code, filesystem erasure, authenticated history or an alien architecture.

The versioned source `v0.1.0` tag is unchanged and remains immutable.
