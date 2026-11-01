# Getting started — Phase 1 fingerprint library

TOMBSTONE has a working **C99 SHA-256 library**, not yet a command-line product. Phase 1 hashes **caller-supplied bytes**. It does not delete files, witness deletions, or create receipts.

## Requirements (Ubuntu)

\`\`\`sh
sudo apt-get install build-essential pkg-config libssl-dev python3
git clone https://github.com/QSOLKCB/TOMBSTONE.git
cd TOMBSTONE
\`\`\`

On systems with the Phase 1 PR merged:

\`\`\`sh
make                       # build/libtombstone.a
make test                  # standalone C99 unit/integration tests
make reproducibility       # compare independent reproducible builds
make sanitizer-test        # ASan + UBSan instrumented tests
make docs-check            # preserve Phase 0 documentation and toy fixtures
\`\`\`

The ABI is in [include/tombstone/fingerprint.h](include/tombstone/fingerprint.h), with [annotated examples and FFI rules](docs/FINGERPRINT_API.md). Use the API by linking against \`build/libtombstone.a\` and the system OpenSSL crypto library (\`pkg-config --libs openssl\`). No executable \`tombstone\` command exists yet.

## What the tests establish

Standard SHA-256 known-answer vectors for empty input, \`abc\`, the longer FIPS test string, a million \`a\` bytes, plus binary data (\`0x00\`, \`0xff\`, \`0x80\`), one-byte streaming, error codes, null-pointer handling, huge-length early rejection on 64-bit, post-final states, external C99 linkage, sanitizer instrumentation, and static-archive repeatability on the tested toolchain.

Those tests do **not** prove secure deletion, hash preimage resistance by experiment, an authenticated receipt history, or cross-platform reproducibility beyond the tested environments.

## Existing toy receipt documentation

The *unimplemented* v1 proposal remains at [machine/schemas/receipt-v1.schema.json](machine/schemas/receipt-v1.schema.json); example receipts are synthetic and validated by \`make docs-check\`. Human explanations are in [docs/](docs/INDEX.md). A before/after hash mismatch never identifies which bytes were removed.

For implementers: read [AGENTS.md](AGENTS.md), [INVARIANTS.md](INVARIANTS.md), and [SECURITY.md](SECURITY.md).
