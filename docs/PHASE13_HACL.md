# Phase 13 — Optional HACL* SHA2-256

The original OpenSSL backend remains the default. An optional backend uses
unmodified SHA2-256 generated C copied from pinned upstream HACL*.

Native C99: `make SHA256_BACKEND=hacl test`
Rust CLI/TUI: `TOMBSTONE_SHA256_BACKEND=hacl cargo test --workspace --offline --locked`

Source provenance: `vendor/hacl-star/UPSTREAM.md` and MIT distribution license
`vendor/hacl-star/dist/LICENSE.txt`. Upstream revision:
`f557259007db9933442dde10aa995c1b00bd3446`.

The HACL* streaming update API consumes uint32_t lengths; the TOMBSTONE
adapter chunks larger input lengths while retaining TOMBSTONE's SHA-256
64-bit bit-length maximum. Backend errors return explicit status codes,
and the caller's output is only written on success.

The verification strategy compares OpenSSL and HACL* through the native C99
and Rust CLI, including frozen canonical JSON receipt bytes, with GCC/Clang
on independent Linux x86-64 and ARM64 environments. Nothing changes the
published v0.1.0 release or default OpenSSL configuration.

**Trust boundary:** Upstream HACL* verifies a particular SHA2-256 primitive
at a specified proof/extraction revision. The new TOMBSTONE adapter,
allocation, multi-chunk handling, C/Rust ABI, generated machine code and
hardware are NOT automatically formally verified. Executed parity and
regression checks provide evidence, but do not close all those premises.
