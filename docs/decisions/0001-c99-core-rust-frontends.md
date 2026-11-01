# ADR-0001: C99 as sole evidence engine; Rust CLI/TUI; optional GTK4

**Status:** Proposed (documentation baseline)  
**Date:** 2026-11-01

## Context

Deletion receipts need deterministic, binary-safe operations and portable verification. Humans and agents need practical terminal workflows; some users may prefer a desktop app. Multiple implementations of content semantics risk inconsistent evidence.

## Decision

1. C99 library is authoritative for byte checks, SHA-256, receipt encoding and verification.
2. Rust supplies a narrow safe FFI adapter and two interfaces: automation-friendly CLI and human-oriented TUI.
3. A GTK4 frontend, preferably Rust gtk4-rs, can be added later and remains optional.
4. Narrative documents reside under root/\`docs/\`, machine schemas and examples under \`machine/\`.
5. Use the existing Apache-2.0 repository license until the maintainer decides otherwise.

## Consequences

**Benefits:** low-level portable core, consistent receipt hashes, safe-ish interface boundaries, headless operation, and optional GUI packaging.

**Costs:** C ABI lifetime management, cross-language build/release and interoperability testing, portable SHA-256 backend selection, and potential Rust GUI dependency weight.

## Rejected alternatives

- Three independent hashing/receipt implementations (semantic drift).
- GUI-first product with C99 as an incidental wrapper (wrong dependency direction).
- Treating snapshot diff as hard proof of exactly deleted bytes (unsupported claim).
