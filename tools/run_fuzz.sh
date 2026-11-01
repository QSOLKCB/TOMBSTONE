#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Bounded deterministic libFuzzer + Address/UndefinedBehaviorSanitizer.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
RUNS=$(printenv FUZZ_RUNS || printf '%s\n' 2000)
CLANG=$(printenv FUZZ_CLANG || printf '%s\n' clang)
BUILD_DIR="$ROOT/build/fuzz"
case "$RUNS" in
  ''|*[!0-9]*) echo "FUZZ_RUNS must be a nonnegative integer" >&2; exit 2 ;;
esac
mkdir -p "$BUILD_DIR"
for target in receipt splice; do
    "$CLANG" -std=c99 -O1 -g -Wall -Wextra -Wpedantic -Werror \
        -fno-omit-frame-pointer -fsanitize=fuzzer,address,undefined \
        -I"$ROOT/include" "$ROOT/src/crypto/fingerprint.c" \
        "$ROOT/src/core/deletion.c" "$ROOT/src/encoding/receipt.c" \
        "$ROOT/tests/fuzz/fuzz_$target.c" -lcrypto \
        -o "$BUILD_DIR/fuzz_$target"
    mkdir -p "$BUILD_DIR/corpus_$target"
    if [ "$target" = receipt ]; then
        cp "$ROOT/machine/examples/"*.json "$BUILD_DIR/corpus_receipt/"
        printf '%s' '{"version":1,"version":1}' > "$BUILD_DIR/corpus_receipt/duplicate.json"
        printf '%s' '{"version":1e999}' > "$BUILD_DIR/corpus_receipt/overflow.json"
        printf '%s' '{"kind":"\uD800"}' > "$BUILD_DIR/corpus_receipt/surrogate.json"
    else
        printf '%s' "1 2 3 4 5" > "$BUILD_DIR/corpus_splice/toy"
        printf '\000\377\200\001\002\000\377\012' > "$BUILD_DIR/corpus_splice/binary"
    fi
    "$BUILD_DIR/fuzz_$target" "$BUILD_DIR/corpus_$target" \
        -seed=1847 -runs="$RUNS" -max_len=4096 -timeout=5 -print_final_stats=1
    printf 'PASS: %s bounded Clang libFuzzer iterations: %s\n' "$target" "$RUNS"
done
