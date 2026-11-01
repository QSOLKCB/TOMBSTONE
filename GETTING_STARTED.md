# Getting started — C99 Phases 1–2

TOMBSTONE now has a SHA-256 core and a **caller-supplied deletion-splice verifier**, not a user CLI. It reads raw byte buffers, hashes them, and can mathematically verify a reported deletion; it does not edit files, collect editor history, or serialize receipts.

## Ubuntu dependencies and tests

\`\`\`sh
sudo apt-get install build-essential pkg-config libssl-dev python3
git clone https://github.com/QSOLKCB/TOMBSTONE.git
cd TOMBSTONE

make                  # builds build/libtombstone.a
make test             # fingerprinting, splice witnessing, independent C99 API linkage
make sanitizer-test   # address and undefined-behaviour sanitizer tests
make reproducibility  # two clean deterministic archive builds
make docs-check       # existing synthetic receipt fixture checks
\`\`\`

The two public headers are [fingerprint.h](include/tombstone/fingerprint.h) and [deletion.h](include/tombstone/deletion.h). Begin with [Phase 2's API walkthrough](docs/DELETION_WITNESS.md) for the exact-splice contract. The [Phase 1 fingerprint guide](docs/FINGERPRINT_API.md) still applies.

## Conceptual example

\`\`\`text
before: 1 2 3 4 5
removed: 3 4␠  (4 bytes at offset 4)
after:  1 2 5
\`\`\`

\`tb_witness_delete\` checks the **exact byte relationship** and returns only lengths and SHA-256 digests. \`tb_observe_transition\` checks before and after but makes **no deletion claim**. These are two different levels of supplied evidence, not proof a historical edit occurred.

The machine receipt v1 schema in [machine/](machine/README.md) is **still a Phase 3 proposal**; \`make docs-check\` is a restricted fixture checker, not a production receipt parser/verifier. Read [SECURITY.md](SECURITY.md) before using secret material.
