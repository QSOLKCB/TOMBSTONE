# Phase 17 — Direct C99 chain rejection and retained-head evidence

This is the first **post-Phase-16** incremental A05 closure milestone.
It preserves the authoritative C99 implementation exactly at Git blob
\`6fe3e8014e9c38ea42c43b9133f026967a4158e3\`, all frozen receipt-v1
golden hashes and the published v0.1.0 archive. It does **not** replace,
rewrite, or resign any receipt.

## What is actually checked

1. A direct-inclusion [CBMC harness](../formal/cbmc/chain_v17_harness.c)
   compiles the real \`src/encoding/receipt.c\` and targets the public
   \`tb_receipt_verify_chain\` function. It checks:
   - null receipts for zero and bounded nonzero counts yield
     \`TB_ERR_ARGUMENT\` before accessing receipts;
   - a valid nonnull pointer and zero count yield \`TB_ERR_ARGUMENT\`;
   - an oversized count \`SIZE_MAX\` yields \`TB_ERR_ARGUMENT\` before
     any array access;
   - an invalid genesis predecessor flag yields \`TB_ERR_MISMATCH\`
     without modifying the tested caller fields.
   These paths intentionally return before computing a receipt hash.
   Their bounded proof does not depend on assuming OpenSSL or HACL* is
   correct, and cannot be projected onto success paths.

2. An [adversarial native C99 program](../tests/formal/test_chain_v17.c)
   uses the actual production public API, reading the three frozen v1
   fixtures and executing all six possible orderings, chain prefixes,
   correct and incorrect supplied trusted heads, per-record digest
   tampering, bad predecessor links/states, invalid array lengths,
   and a newly constructed locally consistent genesis record that
   does **not** match the previously retained fixture head. This
   runtime evidence exercises both real OpenSSL and opt-in HACL*.

3. [Phase 17 CI](../.github/workflows/phase17-chain.yml) requires
   Linux x86-64/AArch64 × GCC/Clang × OpenSSL/HACL. It uses pinned
   CBMC 6.11.0 with mandatory bounds, pointers, integer-overflow and
   complete unwinding assertions. The
   [source identity gate](../tools/check_phase17_evidence.py) pins the
   actual C99 source, bounded harness, native regression and three
   unmodified fixture files. Negative controls reject changed,
   missing or symlinked inputs. Older Phase 14 and 16 source-identity
   gates run unchanged.

## What remains conditional

A complete chain verification is only as strong as its receipt parsing,
domain-separated canonical SHA-256, local predecessor pointers and the
source-to-binary/hardware/OS assumptions. No proof has been discharged
here for arbitrarily long chains, non-prehash paths, complete receipt
encoding/parsing, actual SHA algorithm correctness or external provider
integrity. A matching *caller-supplied* trusted head is not evidence that
the head was obtained, maintained or timestamped independently.
Correctly replayed source bytes do not prove authorship, real filesystem
operations or storage-medium erasure.

Phase 17 **advances** issue #16 but does **not close** it. Issues #15,
#17 and #18 remain tracked in the existing assumption ledger.
Future formal work must refine the complete production hashing and
receipt checks rather than reclassifying a modeled/bounded result as
an unbounded proof.

## Run directly

\`\`\`sh
python3 tools/check_phase17_evidence.py
python3 tests/formal/test_phase17_evidence_gate.py
python3 tools/check_phase14_evidence.py
python3 tools/check_phase16_model.py
make SHA256_BACKEND=openssl test
gcc -std=c99 -Wall -Wextra -Wpedantic -Werror -Iinclude \
  tests/formal/test_chain_v17.c build/libtombstone.a \
  $(pkg-config --libs openssl) -o /tmp/tombstone-phase17-chain
/tmp/tombstone-phase17-chain
\`\`\`

These commands are reproduction instructions, not claims of execution.
Only **actual, exact-head passing CI** and independent Codex review
constitute this milestone's merge acceptance evidence. No automatic
merge or stable tag is authorized.
