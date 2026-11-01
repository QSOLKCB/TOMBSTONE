# Phase 8 — Direct C99 symbolic verification

The CBMC harness includes the **actual production** `src/core/deletion.c`, with nondeterministic byte inputs up to **four bytes**. It does not reimplement the code under test. Hashing is an explicit success-only synthetic dependency, NOT production cryptographic verification.

Run with CBMC 6.x installed (or use the PR's Docker-pinned CI):

```sh
cbmc --function check_witness --unwind 16 --unwinding-assertions --bounds-check --pointer-check --signed-overflow-check --unsigned-overflow-check -I include formal/cbmc/splice_harness.c
cbmc --function check_observe --unwind 16 --unwinding-assertions --bounds-check --pointer-check --signed-overflow-check --unsigned-overflow-check -I include formal/cbmc/splice_harness.c
```

A GCC syntax check is *not* a completed proof. CBMC must exit successfully with all unwinding assertions discharged. The bounded result does not establish arbitrary-length C99 correctness. See `docs/FORMAL_VERIFICATION.md`.
