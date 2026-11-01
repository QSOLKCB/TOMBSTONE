# Pinned HACL* SHA2-256 distribution

Upstream: https://github.com/hacl-star/hacl-star
Exact upstream revision: f557259007db9933442dde10aa995c1b00bd3446

Vendored generated source under vendor/hacl-star/dist/gcc-compatible and
KaRaMeL support headers under vendor/hacl-star/dist/karamel are copied
without modification from that revision. The distribution uses MIT licensing,
while some KaRaMeL headers offer both Apache-2.0 and MIT. Source license
notices are preserved. The copied upstream distribution license is at
dist/LICENSE.txt. The new TOMBSTONE adapter is Apache-2.0.

Only opt-in HACL* builds use these files. The default OpenSSL engine, v1
receipt schema and frozen v0.1.0 release are unchanged.

HACL*'s upstream F*/Low* verification applies to its specified primitive
and assumptions. It does not automatically prove this adapter's memory,
chunking, Rust FFI, compiler, linker, hardware or the actual historical
deletion of information.
