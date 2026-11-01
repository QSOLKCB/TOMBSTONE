# Phase 7 release gate — TOMBSTONE

**Status: Phases 0–7 merged; post-merge CI verified on `d6ae7d4`. A separate release-candidate packaging PR generates the actual source asset and checksum manifest. This is not a tag, release, signature or security certification.** The maintainer owns the final tag decision.

## Required gates before any immutable tag

1. **Exact-tree preservation:** compare Phase 7 against merged main.
   Preserve all Phase 1–6 C99 headers, implementations, tests and Rust UIs.
2. **Executed CI:** GCC/Clang C99 tests, ASan/UBSan, documentation,
   Rust CLI/TUI/optional GTK, bounded libFuzzer and independent receipt replay.
3. **Architecture breadth:** run Linux x86-64 and ARM64 checks. Record
   architecture/toolchain in logs; do not infer non-Linux or 32-bit support.
4. **Golden continuity:** existing v1 receipt commitments must remain:
   `3917b3dc420ddb728616ee3834867664a7012aa5a4c127e56c65651f1ac4dbde`,
   `ba68ca51013bb7a475b2d9991cf59607a1c75dfe34e73a4d1ed9a515a8d02914`,
   `84c0b5f9e478c284553822fb95fe31a72ce71a35070e963d67c328fb777f25e6`.
   A wire change requires a NEW protocol version.
5. **Privacy review:** deletion witness ≠ historical proof; no secure erasure;
   low-entropy commitments can be dictionary-guessed; a local chain is
   re-writable without an independently trusted head.
6. **Review discipline:** Codex/independent reviewer must examine the
   **exact PR head SHA** and report no actionable correctness defects.
   Approval on another SHA does not carry forward.
7. **Release evidence:** record merged source SHA, exact tag target, CI run
   links, toolchain versions, release asset SHA-256 manifest and limitations.
   Tag immutably only after the maintainer explicitly approves.

## What these checks establish

- `sh tools/run_fuzz.sh`: bounded deterministic Clang libFuzzer with **nonrecovering UBSan** and ASan
  and public synthetic inputs, testing parser failure immutability, valid
  canonical roundtrips, splices and mutations. NOT a proof of bug absence.
- `tools/check_portability.py`: independent hashlib plus restricted ASCII
  canonical JSON oracle compared with genuine Rust CLI -> C99 outputs from
  GCC and Clang builds. The Python oracle never ships as production logic.
- `make sanitizer-test`: normal C99 tests instrumented separately from fuzz.

## Out of scope

Secure erasure, authenticated real-world deletion, author/time signatures,
key management, network services, confidential commitments and a formal
security certification. No external trusted anchor is automatically produced.

## Release decision record — complete AFTER review and merge

| Field | Current value |
| --- | --- |
| Candidate tag | Proposed `v0.1.0` — not created |
| Exact reviewed Phase 7 head | `399a18a5449ca9f54df08f5468a363ac0b159b19` (no actionable findings) |
| Merged source commit | `d6ae7d4016eb4efff6a684737711d809ec9d256f` |
| x86-64 / ARM64 evidence | Completed: push run [41294274468](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41294274468) |
| GCC / Clang replay | Completed: push run 41294274468, Linux x86-64 + aarch64 |
| Fuzz evidence | Completed: 2,000 receipt + 2,000 splice iterations, fail-fast UBSan |
| Known limitations | Pending review |
| Asset checksum manifest | Produced by `tools/package_candidate.sh` and uploaded by the source-candidate workflow when successful; never predeclare digest values |
| Immutable tag | Not created |

Full post-merge run details are in [the v0.1.0 evidence record](../release/v0.1.0/POST_MERGE_EVIDENCE.md). Download the produced Actions artifact, inspect and independently verify `SHA256SUMS.txt` before authorizing any tag. **A green workflow is necessary but insufficient for a release.**

**Sanitizer gate regression:** `tools/check_sanitizer_gate.sh` deliberately triggers signed integer overflow in an isolated synthetic binary. It requires UBSan to report an error **and** return nonzero. `tools/run_fuzz.sh` also builds with `-fno-sanitize-recover=undefined` and sets `UBSAN_OPTIONS=halt_on_error=1`. This prevents recoverable undefined-behaviour reports from being mislabelled as passing fuzz runs.
