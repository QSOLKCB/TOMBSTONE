# Phase 14 — Actual C99 receipt-v1 proof and negative evidence

This milestone works against the **production**
[src/encoding/receipt.c](../src/encoding/receipt.c), not a separate toy JSON
implementation. The original C99 ABI, SHA-256 hash domain, 3 frozen receipt
files, OpenSSL default, HACL* opt-in backend, and v0.1.0 release remain unchanged.

## Specification boundary

TOMBSTONE receipt v1 is a **restricted ASCII schema** using fixed object keys,
lowercase hexadecimal SHA-256, safe nonnegative integers, precisely defined
receipt kinds, and sorted compact JSON when *encoding*. It is not a general
Unicode JCS/RFC 8785 implementation. The parser may accept semantically
equivalent reordered/whitespace-extended JSON and escaped ASCII keys; when
encoded, a validated receipt uses one canonical representation.

The hash is calculated as SHA-256 of
\`"TOMBSTONE-RECEIPT-V1\n" || canonical_body_without_receipt_hash\`.
Hashing, C allocation, source-to-binary compilation and any F*/HACL* proof
remain explicit dependencies, not automatically proved by parser lemmas.

An unanchored chain verifies **local linkage only**:
- record zero has no predecessor;
- every later record contains the previous record's 32-byte receipt hash;
- every record's own digest matches its canonical body;
- an optional trusted head equals the last record's hash.
A trusted head must be externally obtained and retained to prevent
whole-chain re-creation. Neither a chain nor a witness proves which
historical file operation occurred, author identity, clock time or erasure.

## Actual source proof targets

| Property | Exact production path | Technique | Status/limitation |
| --- | --- | --- | --- |
| Decimal accumulation never exceeds MAXN on accepted digits | \`number\` -> \`decimal_step\` | ACSL Frama-C/WP with \`-wp-rte\` | Requires executed all-goals CI; covers arithmetic helper, not complete parser |
| Duplicate-bit predicate gives exact seen/unseen result | \`object_fp\`, \`tb_receipt_parse\` -> \`unseen_field\` | ACSL Frama-C/WP | Field-name identification, mask invariants and entire JSON parser are separate |
| Numeric parsing respects bounded cursor and decimal prefix | actual \`number\` | CBMC 6.11.0 direct inclusion | Bounded 1–4 digit symbolic inputs; not large/unbounded integer proof |
| String output and whitespace cursors stay bounded | actual \`string\`, \`ws\` | CBMC 6.11.0 direct inclusion | 0–4 input bytes; not all Unicode escape paths |
| Reject duplicate/unknown fields, malformed values and tampering | actual C99 \`tb_receipt_parse\` | Adversarial native tests | Executed negative controls, not universal theorem |
| Public no-write-on-error, chain/tamper and encoding guards | actual \`tb_receipt_encode\` and \`tb_receipt_verify_chain\` | Native OpenSSL/HACL* GCC/Clang x86-64/ARM64 | Executed fixture scope, not universal proof |

Every formal run requires nonzero, fully discharged obligations and mandatory
CBMC loop unwinding/bounds/pointer/integer-overflow checks. Logs are retained
even when a check fails. \`tools/check_phase14_evidence.py\` pins the actual
production source, the two formal overlays and all three historical v1
fixture Git blobs. Any change must receive new proof evidence.

## Repeat locally

\`\`\`sh
python3 tools/check_phase14_evidence.py
make SHA256_BACKEND=openssl test
cc -std=c99 -O2 -Wall -Wextra -Wpedantic -Werror -Iinclude \
  tests/formal/test_receipt_adversarial.c build/libtombstone.a \
  $(pkg-config --libs openssl) -o /tmp/tombstone-receipt-adversarial
/tmp/tombstone-receipt-adversarial
make SHA256_BACKEND=hacl test
python3 tools/check_docs.py
\`\`\`

CI workflow: [formal-receipt-v14.yml](../.github/workflows/formal-receipt-v14.yml).
Frama-C 32.1 and CBMC 6.11.0 are run using pinned Docker images / versions.
Logs, actual results, and failures must be read at the **exact PR head**;
running these commands is not itself evidence of their success.

## Remaining acceptance gates for issue #16

The following are **not yet proved**: unbounded ACSL/WP contracts for the full
\`tb_receipt_parse\`/JSON string scanner, \`format_json\`/canonical serializer,
all-path public no-write guarantees, unbounded chain invariants, and a checked
refinement from hash-domain construction to the selected real SHA provider.
Compiler/ABI, hardware and independent anchoring are also open. Do not
represent helper-level proofs or green fixture tests as closing these gaps.

Independent Codex exact-head review and all mandatory CI checks are required
before any maintainer merge. This phase is additive, never a historical rewrite.
