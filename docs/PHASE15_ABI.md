# Phase 15 — Target-specific Rust FFI and executable trust boundary

Phase 15 targets the remaining gap between the authoritative C99
implementation and its Rust CLI/TUI consumers. The following results are
**executable observations**, not a theorem of verified compilation.

## Exact target/ABI matrix

The [Phase 15 Actions workflow](../.github/workflows/phase15-abi.yml)
builds on Linux Ubuntu 24.04 x86-64 and ARM64, with GCC and Clang,
separately for default OpenSSL and optional HACL* SHA-256 (eight combinations).
Each job uses the runner's native C compiler, Rust toolchain and linker.

The test-only [C99 layout oracle](../tests/phase15/abi_layout.c) measures
\`sizeof\`, C99 alignment, \`offsetof\`, enum representation/discriminants,
status values, the 32-byte SHA digest and ABI version constants. An in-crate
Rust test compares the observed C measurements with \`std::mem::size_of\`,
\`align_of\` and \`offset_of!\` of the **actual** private \`repr(C)\`
\`EvidenceRaw\` and \`ReceiptRaw\` structs, not a copied reference layout.
The C oracle never enters the shipped static archive or exported API.

The Rust FFI error-path test makes direct calls to the compiled C99 functions
to check status propagation, read-only input lifetime and unchanged *fields*
of Rust output structures on errors. It additionally checks untouched digest
and output JSON bytes, plus the \`written\` length on a capacity error.
These tests use valid disjoint Rust-owned pointers. They are **not** a proof
against undefined behavior for arbitrary forged pointers or of raw padding.

## CLI cap and provenance constraints

The CLI test creates a sparse synthetic file at exactly 64 MiB and
requires successful hashing. It then extends that file to 64 MiB + 1
and requires \`hash\` and \`verify\` to reject the input before passing bytes
to the C99 core, with exit code 2, no stdout, and path-independent stderr.
The TUI/GTK remain transport only and keep their separate workflows.

The Actions matrix builds **two isolated release executables** for
the same compiler/backend/architecture configuration. The gate compares
their complete file hashes and lengths, rejects mismatches, and emits a JSON
target receipt with the source commit, selected source Git blobs, compiler,
Rust/Cargo/archive-tool versions, target architecture, pointer width, backend,
and executable SHA-256. Negative controls prove missing/different binaries
cannot receive a success receipt. Source/test identifiers are captured, not
automatically conferred with proof status.

Re-run commands (Linux):

\`\`\`sh
CC=gcc TOMBSTONE_SHA256_BACKEND=openssl cargo test --workspace --offline --locked
python3 tests/phase15/test_build_receipt_gate.py
# Build two isolated release artifacts before invoking:
python3 tools/phase15_build_receipt.py --first /path/to/a/tombstone \
  --second /path/to/b/tombstone --compiler gcc --backend openssl \
  --output /tmp/phase15-target-evidence.json
\`\`\`

## What remains *unproved*

Matching C and Rust layouts on two host architectures does not prove all
calling conventions, FFI pointer provenance, aliasing/lifetimes, optimizer
soundness, source-to-machine preservation or arbitrary memory safety.
Repeated identical bytes are reproducibility evidence, **not** proof that
those bytes implement the source specification. Neither GCC nor Clang
becomes formally verified by passing this matrix. CompCert/translation
validation is a separate research path and has not been exercised against
these exact released binaries. HACL*/OpenSSL/allocator/linker/libc/OS/hardware
behaviour are external premises.

No TOMBSTONE hash, receipt wire format, native C API, static archive
contents, historical receipt fixtures or \`v0.1.0\` release is changed.
A locally verified chain still says nothing about author, timeline, or secure
erasure without external evidence.

**Merge discipline:** independent Codex review on the final SHA, all
exact-head CI green, clear executed-versus-inferred classification, and
maintainer merge decision. Keep Phase 15 issue #17 open for any remaining
formal compiler and ownership proof obligations.
