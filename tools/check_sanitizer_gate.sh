#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Negative control: recovery-enabled UBSan can emit a report and exit 0.
# Require the hardening setup to exit nonzero on deliberate signed overflow.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
CLANG=$(printenv FUZZ_CLANG || printf '%s\n' clang)
if [ "$#" -ge 1 ]; then CLANG=$1; fi
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
"$CLANG" -std=c99 -O1 -g -fsanitize=undefined \
    -fno-sanitize-recover=undefined \
    "$ROOT/tests/hardening/ubsan_intentional.c" -o "$TMP/ubsan_negative"
if UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 \
    "$TMP/ubsan_negative" >"$TMP/out" 2>"$TMP/err"; then
    echo 'FAIL: deliberate UBSan overflow exited successfully' >&2
    exit 1
fi
if ! grep -q 'runtime error:' "$TMP/err"; then
    echo 'FAIL: UBSan negative control exited without reporting UB' >&2
    exit 1
fi
printf '%s\n' 'PASS: deliberate UBSan overflow failed closed (nonzero exit and runtime diagnostic)'
