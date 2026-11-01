# Security and privacy model

**Scope today:** Phase 1 implements a pure C99 SHA-256 fingerprint library using OpenSSL EVP, alongside illustrative documentation fixtures. Deletion witnessing, receipts, secure erasure and user interfaces are not implemented. The new library accepts caller-supplied byte buffers, not filenames, and does not delete or save data. Report security concerns via a private maintainer channel or GitHub's private vulnerability reporting where enabled; do not post real removed secrets in issues.

## Nonclaims

- A hash is **not encryption**, secure erasure, proof a file was actually erased, proof of who edited it, or proof of deletion time.
- Before/after hashes cannot identify which bytes were removed. Only witnessed-and-validated bytes justify an \`explicit-delete\` receipt.
- A hash of a predictable secret (PIN, short token, common phrase) can be brute-forced by guesses. A plain SHA-256 digest may disclose whether a guessed value was deleted.
- Receipt chains offer tamper evidence against changes *relative to an independently trusted hash head*. An attacker can rewrite an unanchored chain wholesale.
- Editors, swap, journals, storage snapshots, backups and caller memory may retain plaintext long after receipt creation.

## Planned controls

Use length-delimited buffers, overflow checks, strict schema/duplicate-key rejection, a cryptographic backend tested against known vectors, limited allocations, no logging of deleted bytes, no mandatory network connectivity, and meaningful error codes. Do not claim zeroisation is sufficient to erase all copies. The core never automatically deletes filesystem data without an explicit future interface, design review and tests.

An optional keyed commitment or external signature/anchor may be evaluated in later phases; neither is part of the current v1 proposal. See [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md).
