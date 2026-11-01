# Phase 18 — Unbounded C99 receipt-chain WP under explicit SHA assumptions

Phase 18 targets the **actual production** tb_receipt_verify_chain in src/encoding/receipt.c for arbitrary valid nonempty chain counts supported by C99 size_t. The proof translation unit is generated from pinned unchanged source Git blob 6fe3e8014e9c38ea42c43b9133f026967a4158e3. Deleting only generated ACSL comments must reproduce the exact source.

## Claimed proof scope (only after executed full WP success)

- Requires 1 <= count <= SIZE_MAX / sizeof(tb_receipt_v1), valid readable receipt array, and if supplied a readable 32-byte trusted head. Invalid pointer and empty-count paths are independently checked by Phase 17 and NOT covered by this conditional contract.
- The real C99 loop verifies genesis (no predecessor), every successor's nonzero has_previous flag, and every successor's previous_hash equal to the preceding receipt_hash.
- If verification succeeds, these relations hold for all count elements; if trusted_head is present, it matches the final receipt hash in all 32 bytes.
- The function never modifies the caller's receipt array or trusted head. Frama-C/WP must prove the loop invariants, variant, caller framing, memory/overflow RTE conditions and success postconditions for arbitrary valid count, without finite unrolling.

## Explicit modular assumptions — NOT separate SHA correctness proofs

1. The production equal32 helper is **assumed** to read its 32-byte inputs without writes and return 1 exactly when those bytes match. Its memcmp implementation has not been independently proved here.
2. The production calculate_hash helper is **assumed** to modify only a separate 32-byte digest output and return one of the listed statuses. Its output bytes can be arbitrary; no SHA-256 correctness, digest value, successful completion, cryptographic security or SHA-provider resource semantics is assumed or proved.
3. Both contracts need independent source/provider refinement. Neither the actual complete receipt parser/encoder nor Rust ABI/compiler/hardware/OS is proved in this phase.

No source change is permitted: the generator proves the insertion-only property at the byte level, and the Phase 14, 16 and 17 identity gates remain enabled. The original v0.1.0 release and all three historical receipt fixtures remain untouched.

The Phase 18 Actions workflow runs pinned Frama-C 32.1 / Alt-Ergo on the actual public function with -wp-rte and -wp-model Bytes, retaining logs. Missing, zero, incomplete or timed-out goals block merge. It also replays the actual C99 chain fixture and trusted-head regressions on GCC/Clang with both real SHA backends.

**Not established:** cryptographic digest correctness, independent custody of trusted-head values, author/time/event identity, historical file deletion or physical erasure. Full A05 and issues #15–#18 remain open until their separate proof requirements are met.

## Reproduction

    python3 tools/phase18_wp_overlay.py --output receipt_v18_proof.c
    python3 tests/formal/test_phase18_overlay.py
    python3 tests/formal/test_phase18_wp_gate.py
    gcc -std=c99 -Wall -Wextra -Wpedantic -Werror -Iinclude -c receipt_v18_proof.c -o /tmp/v18.o

The source overlay is generated as needed; it is not a separate shipped receipt implementation. Only **executed, exact-head complete solver output** can justify a positive proof claim.
