# TOMBSTONE roadmap

Documentation-first scope and release gates; **nothing listed below as planned is implemented** in this PR.

| Phase | Target | Acceptance gate |
| --- | --- | --- |
| **0 — Foundation** | Architecture, invariants, security model, machine receipt proposal, human docs, banner, C99/Rust folders and fixture checks | Docs check passes; no false claims; review approves design |
| **1 — C99 fingerprinting** | Binary-safe SHA-256 core with vetted backend, public minimal C ABI, input length and error handling | C99 tests, standard SHA-256 vectors, sanitizer build and reproducibility |
| **2 — C99 explicit deletion** | Verified splice operations; observed transitions vs witnessed deletion; deterministic receipt production | Positive/negative tests including empty, replacement, repeated bytes, NUL and overflow |
| **3 — Canonical receipts + chains** | Versioned RFC 8785 encoding, full strict parsing, linkage and independent verification | Golden vectors across platforms; malformed/duplicate-key corpus; tamper tests |
| **4 — Rust adapter and CLI** | Safe FFI, deterministic noninteractive CLI/JSON for agents and scripts | Black-box CLI tests; bytes in = bytes out parity; stderr/stdout separation |
| **5 — Rust TUI** | Human inspection, comparison and guided witnessed deletion workflows | Accessibility, terminal fallback, same receipts as CLI |
| **6 — Optional GTK4** | Thin desktop presentation built on the same Rust/C adapter | GTK isolated from headless build; no semantic divergence |
| **7 — Hardening / v1 release** | Cross-arch/OS replay, fuzzing, signed/anchored receipts considered, threat model and packaging | Independently reviewed evidence, immutable tag, released contract |

## Decisions and explicit exclusions

- v1 receipts **do not include** deleted contents or identifiable file paths; toy test fixtures are separate from generated receipts.
- Secure erasure, undelete, remote monitoring, system-wide editor hooks, authentication and signatures are **not** promised.
- A SHA-256 digest of short, guessable information is vulnerable to guessing. Explore optional keyed commitments only after threat-model review; do not conflate them with normal SHA-256.
- Linux-first is sensible for development, but the C99 library should remain portable. GTK is optional, not a condition of core correctness.
- Roadmap phases can be smaller PRs. Each adds automated evidence before it can be marked complete.

## Near-term implementation PRs

1. C99 library skeleton + SHA-256 known-answer vectors.
2. Explicit byte-splice and observed-transition classifications.
3. Strict receipt v1 encoding + verification, replacing documentation-only checker assumptions with product tests.
4. Rust safe adapter and noninteractive CLI; TUI next.

See [docs/decisions/0001-c99-core-rust-frontends.md](docs/decisions/0001-c99-core-rust-frontends.md).
