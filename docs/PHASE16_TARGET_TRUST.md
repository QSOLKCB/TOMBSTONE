# Phase 16 — Target models, external chain heads, and the physical-event boundary

Phase 16 does **not** abolish the last assumptions. It explicitly separates
software relationships from claims about machines, identities and the world.
The original C99 evidence engine, public ABI, canonical receipt-v1 bytes,
SHA-256 choice, and published v0.1.0 source remain unchanged.

## Supported tested target model

[Machine-readable trust ledger](../machine/phase16/trust-boundaries-v1.json)
is checked offline by [the fail-closed gate](../tools/check_phase16_model.py).
The executable [C99 probe](../tests/phase16/target_probe.c) requires:

- Linux test runners, x86-64 or AArch64, with GCC or Clang;
- 8-bit \`char\`, exact-width 32/64-bit unsigned integers and 64-bit
  \`size_t\` / pointers; little-endian memory;
- native C99 enum layout compatible with the tested Rust \`repr(C)\` FFI
  and all three public ABI versions equal to 1;
- valid, disjoint caller buffers, no C undefined behaviour, functioning
  allocators and cryptographic backend, and reliable toolchain/runtime.

The probe and Phase 15 ABI parity measure **one actual runner execution**.
CI executes GCC/Clang × Linux x86-64/AArch64 × OpenSSL/HACL. Neither
executed tests nor passing formal source lemmas can prove all firmware,
processors, DRAM, compilers, instruction sets, kernels, persistent storage,
hostile machines or physical fault behaviour. Unsupported targets must be
modeled and verified separately. The trusted toolchain/OS/CPU boundary is
explicit in A07/A08 rather than being disguised as proof.

## Optional externally retained trusted chain head

\`\`\`sh
# Retrieve this value from a genuinely independent, previously retained
# record under your own custody (NOT from the chain currently being audited).
# It must be exactly 64 lowercase hexadecimal characters.
tombstone verify-chain first.json second.json third.json \
  --trusted-head-file /media/offline-custody/known-head.txt

# Existing literal-head interface still works independently:
tombstone verify-chain first.json second.json third.json \
  --trusted-head 84c0b5f9e478c284553822fb95fe31a72ce71a35070e963d67c328fb777f25e6
\`\`\`

The head file must be a regular, non-symlinked file containing exactly 64
lowercase SHA-256 hex bytes, optionally one terminating LF. UTF-8 BOM,
whitespace, CRLF, uppercase, trailing bytes, stdin \`-\` and directories are
rejected. At most 66 bytes are read. \`--trusted-head\` and
\`--trusted-head-file\` are mutually exclusive; any multiple source options
fail closed. The CLI never creates or overwrites an anchor, logs its path or
contacts any service. It parses bytes and delegates full receipt-chain and
trusted-head comparison to the **existing C99** verifier.

An anchor is *independent* only when its prior retention/integrity can be
established outside the potentially compromised receipt collection. Merely
copying the final receipt's head to another local file at verification time
does not achieve that property. An attacker able to modify both the chain and
the head can fabricate another internally consistent collection. The
new regression demonstrates this: a newly generated valid genesis passes
unanchored, and fails against a previously supplied different head.

A head comparison establishes **equality to the value supplied to the CLI**,
not the value's origin. No trusted timestamp, custody record, author
authentication, key management or signature verification is automatically
provided. In particular, caller-generated timestamps or identity strings
would be assertions, not independent evidence. Signatures remain future
optional work and would require key provisioning, revocation, scope,
timestamp and identity threat models before being used as evidence.

## Three distinct real-world claims

| Classification | TOMBSTONE can show | Additional evidence required |
| --- | --- | --- |
| **Verified byte-splice relation** | Supplied before/removed/after buffers satisfy a claimed offset relationship | A real operation occurred at that location and time |
| **Observed filesystem event** | TOMBSTONE does not monitor deletion or filesystem activity | Independently collected OS/audit log, chain of custody, sensor or trusted observer |
| **Physical storage erasure** | Neither hash nor receipt proves this | Device-specific controller/firmware evidence, storage medium behavior, forensic methods and overwrite/trim/GC assumptions |

The C99 \`explicit-delete\` category is a **witnessed byte relationship**.
It is *not* the third row, and it does not by itself establish the second.
Even filesystem unlink evidence would not prove physical erasure from SSD
cells, backups, snapshots, swap or remote copies.

## Fail-closed tests and evidence discipline

- \`python3 tools/check_phase16_model.py\` checks the actual C99 Git source
  blobs, three unchanged receipt fixtures, immutable \`v0.1.0\` release
  identity, and A01–A09 claim classifications.
- \`python3 tests/phase16/test_model_gate.py\` must reject a forged
  "hardware proved" or "secure erasure" claim, missing/modified source,
  duplicate JSON keys and unsupported target probes. Tests operate on
  isolated copies rather than modifying repository sources.
- \`cargo test -p tombstone-cli -p tombstone-ffi --offline --locked\`
  exercises anchored/unanchored chains, malformed/reordered anchor options,
  invalid file types and path-independent errors.
- [Phase 16 workflow](../.github/workflows/phase16-trust.yml) executes
  the native C99 probe and real CLI/native regressions on eight target
  configurations, saving an observation receipt with the GitHub run/head.
  An executed observation is not a verified compiler/hardware attestation.

**Review gate:** The exact PR head must have green CI, independently reviewed
actionable findings resolved, and explicit maintainer approval to merge.
Do not close the ongoing unbounded SHA provider, whole-receipt, FFI or
source-to-binary proof obligations simply because Phase 16's conditional
trust model is accepted.
