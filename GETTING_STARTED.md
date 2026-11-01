# Getting started — documentation baseline

TOMBSTONE currently has **no C99 engine or Rust interface executable**. These steps validate the repository's example receipt and public toy data; they do not perform real deletion.

## Requirements

- GNU Make (optional; command can be run directly)
- Python 3 (standard library only)
- Git

\`\`\`sh
git clone https://github.com/QSOLKCB/TOMBSTONE.git
cd TOMBSTONE
make docs-check
# equivalent:
python3 tools/check_docs.py
\`\`\`

Check [machine/schemas/receipt-v1.schema.json](machine/schemas/receipt-v1.schema.json), then [machine/examples/explicit-delete-v1.json](machine/examples/explicit-delete-v1.json). Human explanations live under [docs/](docs/INDEX.md); machine JSON is deliberately separate.

## A conceptual example

\`\`\`text
before: 1 2 3 4 5
removed: 3 4␠       (four bytes, beginning at offset 4)
after:  1 2 5
\`\`\`

The toy fixture's four removed bytes are intentionally **public** for testing. In normal operation only their **SHA-256, size, and verified offset** belong in a receipt. The missing bytes cannot be recovered from a hash alone. \`explicit-delete\` is only valid when the exact removed span and resulting buffers are witnessed; snapshots alone produce an \`observed-transition\`.

The example illustrates a contract. **Do not treat it as the output of a released TOMBSTONE binary.** Consult [SECURITY.md](SECURITY.md) before using real confidential data.

## Implementer pathway

Read [AGENTS.md](AGENTS.md), [INVARIANTS.md](INVARIANTS.md), [ARCHITECTURE.md](ARCHITECTURE.md), and [ROADMAP.md](ROADMAP.md). Phases 1–3 construct/verify the C99 engine; Rust CLI/TUI and optional GTK follow.
