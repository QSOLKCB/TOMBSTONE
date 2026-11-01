# Phase 4 — Rust CLI and safe C99 FFI

**Implementation:** \`bindings/rust/\` provides the narrow, safe Rust interface; \`apps/cli/\` provides the \`tombstone\` binary. C99 remains the only implementation of SHA-256, splice witnessing, canonical receipt encoding/parsing and chain validation. Rust parses CLI arguments and file data only.

There are **no third-party Rust dependencies**. Building uses a small Cargo \`build.rs\` to compile the existing C99 source files and link the system OpenSSL \`libcrypto\`; this does not modify or replace the existing Makefile builds. Ubuntu requires \`build-essential\`, \`pkg-config\`, \`libssl-dev\`, \`cargo\`, \`rustc\`. The initial build targets native Linux; cross-compilation requires CC/AR and matching OpenSSL libraries for the intended target.

## Build and test

\`\`\`sh
cargo test --workspace --offline --locked
cargo build -p tombstone-cli --release --offline --locked
target/release/tombstone --help
\`\`\`

\`make rust-test\` and \`make rust-build\` are convenience aliases. The existing \`make test\`, \`make sanitizer-test\`, \`make reproducibility\` and \`make docs-check\` remain valid.

## Commands

\`\`\`sh
# SHA-256 of exact raw file bytes (use '-' for stdin):
tombstone hash tests/fixtures/before.txt

# Before/after observation (deletion is NOT inferred):
tombstone observe tests/fixtures/before.txt tests/fixtures/after.txt

# Explicitly witnessed splice: a removed span, offset, before and after:
tombstone delete tests/fixtures/before.txt tests/fixtures/deleted.txt tests/fixtures/after.txt 4

# Independently chosen predecessor commitment: caller takes responsibility:
tombstone observe before.bin after.bin --previous <64-lowercase-hex>

# Verify a single receipt's syntax and self-hash ONLY:
tombstone verify machine/examples/explicit-delete-v1.json

# Check a genesis-to-head ordered chain, optionally with a trusted final hash:
tombstone verify-chain \
    machine/examples/explicit-delete-v1.json \
    machine/examples/observed-transition-v1.json \
    machine/examples/unchanged-v1.json \
    --trusted-head 84c0b5f9e478c284553822fb95fe31a72ce71a35070e963d67c328fb777f25e6
\`\`\`

**Outputs:** successful evidence operations print exactly one deterministic compact JSON object plus newline on stdout. The C99 engine writes the canonical receipt body; Rust does not reimplement the hashing or wire format. \`hash\` emits \`{"sha256":"...","size":N}\`. \`verify\` emits \`{"receipt_hash":"...","self_hash_valid":true}\`, **never a claim about the entire chain**. \`verify-chain\` emits \`{"chain_valid":true,"count":N,"head":"...","trusted_head_checked":true|false}\`.

**Exit codes:** \`0\` success, \`2\` command/argument error or input above 64 MiB, \`3\` C99 evidence/format/hash/chain verification error, \`4\` file or stdout I/O error. Error text is sent to stderr; stdout remains empty on failure. The tool does not include file paths or raw input bytes in diagnostic output.

**Command-line encoding:** Arguments are read with `args_os()` and validated before any command is executed. Phase 4 accepts UTF-8 argument text only, including filenames. On Unix, filenames or option values containing invalid UTF-8 are **rejected with exit status 2** and a generic `tombstone: command arguments must be valid UTF-8` diagnostic; neither the raw bytes nor the filename are printed. A future OS-native path implementation may broaden filename support without changing receipt semantics. Raw **file contents** and stdin remain binary-safe.

**Input constraints:** each file or stdin input is capped at 64 MiB, to avoid unbounded memory allocation. A single \`-\` can be supplied per command and reads raw stdin bytes; receipts passed to \`verify\` are checked by the C99 parser, which also enforces its own 16 KiB JSON bound. Digests for \`--previous\` and \`--trusted-head\` must be exactly 64 **lowercase** hexadecimal characters. Paths are deliberately excluded from all receipt metadata.

## Trust boundaries

- A checked splice demonstrates consistency of *caller-supplied* before, removed and after buffers. It does not prove an actual historical deletion or secure erasure.
- \`--previous\` attaches a caller-supplied hash; it does **not** validate the previous receipt. Use \`verify-chain\` over the full ordered chain.
- \`verify-chain\` without \`--trusted-head\` checks local consistency, **not authenticity against wholesale rewriting**. Trusted heads must come from an independent trusted source.
- The CLI reads files, including possibly sensitive deleted bytes, into process memory. The receipt contains fingerprints only; plaintext can remain in the source files, process memory, swap, editor backups and caller-controlled stores.
- Short secrets may be guessed from unsalted SHA-256 fingerprints. This is not a confidential deletion or erasure tool.
- TUI and GTK remain Phase 5/6; no interactive prompts, cloud, telemetry or remote access are introduced.
