# Independent receipt replay and platform matrix

**Status:** Phase 7 checks configured; obtain executed results only from the
GitHub Actions runs for the *exact* PR head, not this prose.

The matrix uses `ubuntu-24.04` and `ubuntu-24.04-arm`. On each runner it
builds the real headless Rust CLI twice in isolated target directories:
one using GCC for the native C99 engine, one using Clang. The Python
standard-library test oracle independently checks SHA-256 and fixed-v1
canonical JSON, golden receipts, binary stdin, ordered and anchored chains,
tampered digest, malformed duplicate keys, and byte equality across builds.

The normal native C99 tests run separately. GTK4 and TUI keep their own
isolated workflows; no Python digest logic enters the production library.

**Limit:** These checks do not imply 32-bit, Windows, macOS, big-endian or
all OpenSSL-version coverage. RFC 8785 equivalence is valid only for the
restricted v1 ASCII/lowercase-hex/JSON-safe-integer fields, not arbitrary JSON.

See [release gate](RELEASE_GATE.md) and
[anchoring/privacy](ANCHORING_PRIVACY.md).
