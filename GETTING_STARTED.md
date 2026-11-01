# Getting started — C99 Phases 1–3

TOMBSTONE now has SHA-256 fingerprinting, caller-supplied deletion-splice verification, and canonical receipt/chain validation in C99, **but no user CLI**. It reads raw byte buffers, hashes them, and can mathematically verify a reported deletion; it does not edit files, collect editor history, or serialize receipts.

## Ubuntu dependencies and tests

\`\`\`sh
sudo apt-get install build-essential pkg-config libssl-dev python3
git clone https://github.com/QSOLKCB/TOMBSTONE.git
cd TOMBSTONE

make                  # builds build/libtombstone.a
make test             # fingerprints, splices, receipt vectors/negative parsing, chain checks
make sanitizer-test   # address and undefined-behaviour sanitizer tests
make reproducibility  # two clean deterministic archive builds
make docs-check       # existing synthetic receipt fixture checks
\`\`\`

The public headers are [fingerprint.h](include/tombstone/fingerprint.h), [deletion.h](include/tombstone/deletion.h) and [receipt.h](include/tombstone/receipt.h). Read [the Phase 3 API guide](docs/RECEIPT_ENGINE.md) for the new serializer, parser and chain verifier. Begin with [Phase 2's API walkthrough](docs/DELETION_WITNESS.md) for the exact-splice contract. The [Phase 1 fingerprint guide](docs/FINGERPRINT_API.md) still applies.

## Conceptual example

\`\`\`text
before: 1 2 3 4 5
removed: 3 4␠  (4 bytes at offset 4)
after:  1 2 5
\`\`\`

\`tb_witness_delete\` checks the **exact byte relationship** and returns only lengths and SHA-256 digests. \`tb_observe_transition\` checks before and after but makes **no deletion claim**. These are two different levels of supplied evidence, not proof a historical edit occurred.

The machine receipt v1 schema in [machine/](machine/README.md) is now exercised by the C99 Phase 3 parser and the three preexisting golden receipts. \`make docs-check\` remains a separate Python fixture checker, not the engine's verifier. Read [SECURITY.md](SECURITY.md) before using secret material.
