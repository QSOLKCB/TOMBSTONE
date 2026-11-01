# Architecture — C99 core, Rust clients, optional GTK

## Boundary and maturity

This is a staged target design. **Phases 1–2 implement C99 SHA-256 fingerprinting and exact deletion-splice verification**. Phase 2 is merged. Phase 3 provides merged schema-limited RFC 8785 receipt serialization, strict parsing and hash-link validation. Phase 4 merged the safe Rust FFI and headless CLI. Phase 5 merged the Rust ncurses terminal UI. Phase 6 introduces a separate optional native GTK4 desktop frontend (in PR pending review). No filesystem deletion capability is implemented. TOMBSTONE is a receipt system for *witnessed deletions* and *observed transitions*, not an archive of the deleted content.

\`\`\`text
             Human terminal        Agents/scripts          Optional desktop
               Rust TUI              Rust CLI              GTK4 via Rust
                   \                    |                       /
                    +-------------------+----------------------+
                                        |
                                 Rust safe FFI layer
                                   bindings/rust/
                                        |
                                    C ABI (planned)
                                include/tombstone/
                                        |
                                 libtombstone (C99)
                      +-----------------+------------------+
                      |                 |                  |
                  src/core/         src/crypto/       src/encoding/
                 splice checks     SHA-256 adapter    canonical JSON
                      +-----------------+------------------+
                                        |
                                machine/ receipt v1
\`\`\`

**Ownership:** Only C99 is permitted to classify a deletion, hash bytes, construct and validate canonical receipts, or verify the chain. Rust owns UI, arguments, presentation, transport and safe FFI memory handling, never a competing implementation. GTK4 via its native C API in a small Rust UI-only binding is an **optional** frontend, not a runtime dependency of C99, the headless CLI or the ncurses TUI.

### C99 core

**Phase 1 implemented:** `include/tombstone/fingerprint.h` provides a versioned public C ABI for one-shot/streaming SHA-256, hexadecimal output and explicit argument, state, allocation and length errors. `src/crypto/fingerprint.c` delegates cryptography to OpenSSL EVP. Tests and reproducible archive builds run in GitHub Actions. This implementation has no file I/O, no direct deletion, and no receipt parser.

**Phase 2 merged:** `include/tombstone/deletion.h` and `src/core/deletion.c` classify full before/after buffers and validate caller-provided exact deletion splices, returning only hashes, sizes and the verified claimed offset. The output is an in-memory C99 struct, **not** JSON. An observed transition never infers a removed span; multiple offsets can satisfy repeated-byte cases.

**Phase 3 merged:** `include/tombstone/receipt.h` and `src/encoding/receipt.c` produce canonical v1 JSON (strictly limited to fixed ASCII fields and safe integers), parse validated records, recompute SHA-256 commitments and verify genesis/links/optional trusted head. This is a restricted RFC 8785 JCS implementation, **not** arbitrary JSON canonicalization or historical deletion attestation.

**Later phases must add:**

- Additional adversarial hardening and cross-platform ABI evidence beyond the implemented binary-safe APIs.
- Fuzzing, interoperability and independent receipt-chain verification across runtimes, plus optional external anchor/signature transport.
- No network access, telemetry, implicit content retention or automatic filesystem deletion.

### Rust frontends

- `bindings/rust/`: Phase 4 safe Rust FFI, with only an internal unsafe C ABI surface, Rust slice/ownership checks and native C99 archive linking.
- `apps/cli/`: Phase 4 noninteractive commands, pipe-safe deterministic JSON and stderr diagnostics, stable exit codes; no implicit prompts.
- `apps/tui/`: Phase 5 Rust ncurses TUI, using the same safe adapter for guided evidence/chain workflows; no secondary cryptographic implementation.
- `apps/gtk/`: Phase 6 optional GTK4 desktop UI. Separate Cargo workspace (excluded from root), using Phase 5 workflow functions and the same authoritative C99 FFI.

**Phase 4 build boundary:** Cargo build scripts compile the unchanged C99 source into a private native static archive linked with system OpenSSL. Rust never duplicates receipt serialization, hashing or evidence classification. The CLI reads bounded caller-controlled file bytes (or stdin) and supplies them to C99; the core itself still performs no filesystem I/O.

**Phase 5 terminal boundary:** The TUI links system ncursesw and reads selected files within caps; it can export C99 canonical receipts only by an explicit create-new action, never overwrites them, and does not silently delete source data. The C99 archive and headless CLI still build without ncurses. Rust ncurses handles only UI state, scrolling and prompts. GTK builds separately and has no influence on ncurses or headless CLI dependency sets.

**Phase 6 desktop boundary:** The GTK app is a standalone Cargo workspace with its own native GTK4 dependencies. Rust uses minimal GTK4 C ABI calls solely to build windows, gather UTF-8 path input and display C99-derived results. The same Phase 5 workflow functions enforce size limits, chain validation, canonical exports and create-new-only saving. GTK does not change or replace the root Cargo workspace, C99 library or headless CLI.

### Evidence classes

| Kind | Inputs witnessed | What can be claimed |
| --- | --- | --- |
| \`explicit-delete\` | Before, after, exact removed bytes, byte offset; splice verified | These bytes were supplied and verified as the removed span |
| \`observed-transition\` | Before/after bytes or trustworthy fingerprints | An observed change, **not** a proven removal |
| \`unchanged\` | Identical before/after byte contents | No detected change; **not** a deletion |

Phase 2 validates `before == prefix || removed || suffix` and `after == prefix || suffix` for a **caller-supplied** offset; it does not prove a real-world edit occurred. An arbitrary diff is not a trustworthy statement of which exact bytes a person deleted: insertions, replacements and repeated substrings permit ambiguities. Source attribution and independent witnessing require separate mechanisms.

### Candidate receipt v1

The machine-readable schema is [machine/schemas/receipt-v1.schema.json](machine/schemas/receipt-v1.schema.json). The digest over a receipt is:

\`\`\`text
receipt_hash = SHA256(
    ASCII("TOMBSTONE-RECEIPT-V1\n")
    || RFC8785_JCS(receipt object without receipt_hash)
)
\`\`\`

All proposed v1 fields use fixed ASCII strings, 64-character lowercase hex digests, null, and nonnegative integers constrained to the JSON-safe range. The C implementation produces valid RFC 8785 output for the restricted v1 schema (fixed ASCII literals and bounded nonnegative integers), not arbitrary JSON values. The documentation checker remains separate and is not a production verifier. \`previous_receipt_hash\` commits to the preceding receipt hash; \`null\` marks a genesis receipt. Anchoring a chain head externally is necessary for meaningful tamper-evidence against wholesale rewriting. This does **not** establish authorship or a verified chronology.

### Persistence and privacy

Persist only receipt metadata: event kind, digests, byte lengths, optional verified deletion offset and previous link. Do not serialize deleted bytes. No paths, freeform metadata, user IDs or timestamps in the minimal v1 receipt. Data can still persist in buffers, temporary files, swap, editor histories, filesystem journals and backups. SHA-256 of a short secret is susceptible to dictionary guessing; v1 is *not* a confidentiality primitive.

### Repository layout

\`\`\`text
docs/                      human explanations, threat model, decisions, asset
machine/                   JSON Schema and machine-readable example receipts
include/tombstone/         public C99 fingerprint and deletion-evidence headers
src/{core,crypto,encoding}/ C99 implementation of splices, SHA-256 and receipts
bindings/rust/             implemented safe Rust C99 adapter
apps/cli/                   implemented headless Rust CLI (Phase 4)
apps/tui/                   merged Rust interactive ncurses UI
apps/gtk/                   isolated Phase 6 Rust/GTK4 desktop frontend (in PR)
tests/{unit,integration,fixtures}/ validation targets + public toy fixture
tools/                     docs/fixture validation
examples/                  later user-facing usage examples
.github/workflows/         documentation fixture CI
\`\`\`

Initial implementation should land in independent reviewable PRs and prove the invariants in [INVARIANTS.md](INVARIANTS.md), with no promises of real deletion or secure erasure before tests exist.
