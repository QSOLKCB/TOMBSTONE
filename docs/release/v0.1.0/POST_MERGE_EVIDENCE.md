# TOMBSTONE v0.1.0 — post-merge release evidence

**Status:** source-only release candidate evidence. No release tag has been created; no executable assets have been packaged. This is an evidence record, not a security certification.

## Fixed source and review provenance

| Property | Verified value |
| --- | --- |
| Source repository | https://github.com/QSOLKCB/TOMBSTONE |
| Candidate version | `v0.1.0` (proposed) |
| Release source commit | `d6ae7d4016eb4efff6a684737711d809ec9d256f` |
| Merge | [PR #8](https://github.com/QSOLKCB/TOMBSTONE/pull/8) |
| Exact independently reviewed head | `399a18a5449ca9f54df08f5468a363ac0b159b19` |
| Review outcome | No actionable correctness or security findings for the exact head |
| Merge method | GitHub merge commit, with source commit `d6ae7d4016eb4efff6a684737711d809ec9d256f` |
| Previous baseline (PR #8 base) | `d01dd953a8445fee12c864409f0f79451cff0f05` |
| Source release scope | Git archive of the fixed merge commit (tracked source only; no binary builds) |

## Executed post-merge CI — all checks on the exact release source SHA

All six **push** workflows below were executed against `d6ae7d4016eb4efff6a684737711d809ec9d256f`, not merely the PR head. Each returned `success`.

| Gate | Run | Result |
| --- | --- | --- |
| C99 GCC/Clang, sanitizers, reproducibility | [41294274427](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41294274427) | PASS |
| Rust FFI and CLI | [41294274496](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41294274496) | PASS |
| ncurses TUI and PTY smoke | [41294274516](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41294274516) | PASS |
| GTK4 native build and Xvfb/D-Bus smoke | [41294274493](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41294274493) | PASS |
| Bounded Clang fuzz + GCC/Clang portability replay | [41294274468](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41294274468) | PASS |
| Machine schema/documentation fixtures | [41294274478](https://github.com/QSOLKCB/TOMBSTONE/actions/runs/41294274478) | PASS |

### Executed job-level evidence

- Native C99 GCC job 124811730481: known-answer SHA-256 vectors, witnessed deletion regressions, canonical receipt/chain checks and reproducible archive comparison PASS. Two isolated GCC native archive builds matched SHA-256 `77bbd3b9056a56bf14a593165584a544f208eac5b79abe6e62b7fc24844f1256`.
- Native C99 Clang job 124811730640: same C99 checks PASS; two isolated Clang native archive builds matched SHA-256 `8e6331f77f9fc653982c22cfad99403733ee55eda24c70aec4d93bfaf4d97ec4`. The GCC and Clang archives are **not** claimed to be mutually byte-identical.
- Clang fuzz job 124811730674: deliberate UBSan signed-overflow negative control exited nonzero with a runtime diagnostic; receipt parser and splice fuzzer each completed 2,000 bounded iterations with ASan/UBSan, PASS.
- Linux x86-64 job 124811730819 and Linux ARM64 job 124811730808: independently compiled Rust CLI using GCC and Clang C99 backends; byte-identical receipt output, restricted RFC 8785/hashlib replay, genesis/anchored-chain, binary-input and negative tampering checks PASS on both.
- Both portability runners reported Ubuntu GCC 13.3.0, Clang 18.1.3, rustc 1.99.1; architecture reported `x86_64` and `aarch64` respectively.
- GTK4 job 124811730652: five desktop workflow integration tests PASS, GTK4 activation and repeated activation smoke PASS; second real process forwarded activation over session D-Bus to one existing window PASS. GTK focus on actual Wayland remains compositor-controlled.

## Golden receipt v1 commitments unchanged

- Explicit deletion: `3917b3dc420ddb728616ee3834867664a7012aa5a4c127e56c65651f1ac4dbde`
- Observed transition: `ba68ca51013bb7a475b2d9991cf59607a1c75dfe34e73a4d1ed9a515a8d02914`
- Unchanged: `84c0b5f9e478c284553822fb95fe31a72ce71a35070e963d67c328fb777f25e6`

## Archive and checksum evidence

The **candidate release packaging workflow** creates a deterministic source tarball using `git archive` of precisely `d6ae7d4016eb4efff6a684737711d809ec9d256f` followed by `gzip -n -9`. It builds it twice and requires byte equality, then creates a real `SHA256SUMS.txt` for the generated assets. This paragraph documents the mechanism; it does not by itself assert packaging success.

**Included planned assets:** `TOMBSTONE-v0.1.0-source.tar.gz`, `SOURCE_COMMIT.txt`, `POST_MERGE_EVIDENCE.md`, `SHA256SUMS.txt`. The manifest contains actual computed digests, not a placeholder value. No compiled binary, signing key, signature or attestation is implied.

## Nonclaims and remaining release decision

- No historical deletion/authorship/time attestation or secure erasure.
- A valid splice only proves a mathematical relationship among caller-supplied buffers.
- SHA-256 of guessable removed bytes is not confidentiality.
- A local receipt chain can be completely rewritten without an independently trusted external head.
- Limited executed platforms: Linux x86-64/ARM64; no Windows/macOS/32-bit claim.
- Bounded fuzz checks are not proof that the implementation is defect-free.

The maintainer must explicitly approve the tag after reviewing the candidate archive, the actual manifest, CI evidence, release notes, and any outstanding limitations. **No tag or GitHub Release may be published by the packaging workflow.**
