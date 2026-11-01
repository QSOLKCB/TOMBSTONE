# Phase 8 — Direct C99 symbolic verification

The CBMC harness includes the **actual production** `src/core/deletion.c`, with nondeterministic byte inputs up to **four bytes**. It does not reimplement the code under test. Hashing is an explicit success-only synthetic dependency, NOT production cryptographic verification.

Run with CBMC 6.x installed (or use the PR's Docker-pinned CI):

```sh
cbmc --function check_witness --unwind 192 --unwinding-assertions --bounds-check --pointer-check --signed-overflow-check --unsigned-overflow-check -I include formal/cbmc/splice_harness.c
cbmc --function check_observe --unwind 192 --unwinding-assertions --bounds-check --pointer-check --signed-overflow-check --unsigned-overflow-check -I include formal/cbmc/splice_harness.c
```

A GCC syntax check is *not* a completed proof. CBMC must exit successfully with all unwinding assertions discharged. The bounded result does not establish arbitrary-length C99 correctness. See `docs/FORMAL_VERIFICATION.md`.

## Phase 9 — Frama-C/WP on production C99

`src/core/deletion.c` contains the new private `splice_equal` used by `tb_witness_delete`, with an ACSL equivalence contract and unbounded loop invariants. `sh tools/run_wp.sh` runs Frama-C/WP + Alt-Ergo against **that actual source**, checking runtime errors and requiring that every generated nonzero proof obligation is discharged. The GitHub Actions workflow `.github/workflows/formal-wp.yml` runs it in a versioned Frama-C Docker image and retains the proof log.

**Scope:** only the actual pure splice-relation helper under valid-readable-buffer preconditions. The complete public C99 wrapper, hash provider, compiled binary, Rust FFI, and historical deletion authentication remain unproved. No “formally verified” badge for the whole library until all these boundaries are discharged.
