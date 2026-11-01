# Concept — information that disappears can leave evidence

Given the exact bytes that will be removed *before* they vanish, a tool can compute a hash of the removed span, verify the result of its removal, and issue a receipt storing **only fingerprints, byte lengths and offset**. The removed plaintext itself is not retained in the receipt.

By contrast, after the fact, a changed file digest tells you **only that file bytes differ** (assuming collision resistance). No mathematical operation on two SHA-256 digests reveals the missing characters. Any text diff is an explanation hypothesis, not direct observation of the deletion operation.

## Terminology

- **Fingerprint:** SHA-256 of specific raw bytes.
- **Witnessed explicit delete:** The before stream, exact removed span, original byte offset and after stream were available, and their splice relation was verified.
- **Observed transition:** Before/after fingerprints were compared but the removed span was not witnessed.
- **No-op:** Same bytes, same fingerprints; cannot be counted as a deletion.
- **Receipt:** Versioned machine record storing fingerprints and evidence classification.
- **Receipt chain:** Hash-linked ordering of receipts; authenticity requires independently anchored reference or other assurance.
- **Secure erasure:** A different problem not solved by this system.

The toy example removes \`3 4 \` (including trailing space) at byte offset 4 from \`1 2 3 4 5\`, giving \`1 2 5\`. The fixture contains the bytes openly to permit testing. Real receipts do not.
