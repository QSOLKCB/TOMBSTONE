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

## Immutable upstream source and proof provenance

- HACL* upstream commit: [`f5572590…`](https://github.com/hacl-star/hacl-star/tree/f557259007db9933442dde10aa995c1b00bd3446)
- F*/Low* source for [SHA2 hashing](https://github.com/hacl-star/hacl-star/blob/f557259007db9933442dde10aa995c1b00bd3446/code/hash/Hacl.Hash.SHA2.fst) and [streaming SHA2](https://github.com/hacl-star/hacl-star/blob/f557259007db9933442dde10aa995c1b00bd3446/code/streaming/Hacl.Streaming.SHA2.fst)
- Generated C source: [`Hacl_Hash_SHA2.c`](https://github.com/hacl-star/hacl-star/blob/f557259007db9933442dde10aa995c1b00bd3446/dist/gcc-compatible/Hacl_Hash_SHA2.c), toolchain: F* to KaRaMeL to C; 16 sources/headers and their Git blob identities are checked by `tools/check_hacl_source.py` with no network access.
- License: upstream MIT distribution notice retained; project adapter remains Apache-2.0.

The linked F* files identify the verification lineage but are **not themselves
executed verification logs**. TOMBSTONE has not reproduced the F* proof at this
revision or formally connected its public C99 adapter to the generated digest.
The strict standard C99 build uses `-D_DEFAULT_SOURCE` on Linux so upstream
endian helpers are visible and selectively suppresses pedantic warnings for
the upstream `__int128` extension. This is a platform/toolchain dependency;
portable non-Linux semantics have not been shown.

## Exact-head validation targets

```sh
python3 tools/check_hacl_source.py
make SHA256_BACKEND=openssl test
make SHA256_BACKEND=hacl test
make SHA256_BACKEND=hacl sanitizer-test
TOMBSTONE_SHA256_BACKEND=hacl cargo test --workspace --offline --locked
```

The Phase 13 workflow also checks allocation and update failure injection,
SHA-256 padding/chunk boundaries, >1 MiB of binary streaming input, and all
three frozen v1 receipt fixtures with an independent Python hash oracle and
OpenSSL. These are bounded executed tests **only after their CI runs finish**.
A `uint32_t` backend chunk interface cannot be meaningfully exercised using
invalid large pointers; no >4 GiB memory test or unconditional length-conversion
proof is claimed.

**Outstanding Phase 13 acceptance gates:** separate CBMC/Frama-C adapter
contract proof, reproduced F* proof origin and toolchain versions/receipts,
and an exact-head review (with every CI check green). These are not replaced
by normal test success. Phase 14 and later retain their own boundaries.
