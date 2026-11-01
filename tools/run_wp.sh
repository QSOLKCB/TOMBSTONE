#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Prove actual src/core/deletion.c's splice_equal, not a copy.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
LOG=$(mktemp)
trap 'rm -f "$LOG"' EXIT HUP INT TERM
frama-c -version
if ! frama-c -wp -wp-fct splice_equal -wp-prover alt-ergo -wp-timeout 20 \
    -wp-rte -wp-par 2 -cpp-extra-args="-Iinclude" src/core/deletion.c > "$LOG" 2>&1; then
    cat "$LOG"
    exit 1
fi
cat "$LOG"
python3 tools/check_wp_proofs.py "$LOG"
