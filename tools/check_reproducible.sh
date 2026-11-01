#!/bin/sh
# Compare deterministic archives from two clean builds with identical flags.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TEMP_ROOT=$(mktemp -d)
trap 'rm -rf "$TEMP_ROOT"' EXIT HUP INT TERM
for name in a b; do
    make -s -C "$ROOT" BUILD_DIR="$TEMP_ROOT/$name" all
    test -f "$TEMP_ROOT/$name/libtombstone.a"
done
if ! cmp -s "$TEMP_ROOT/a/libtombstone.a" "$TEMP_ROOT/b/libtombstone.a"; then
    echo 'FAIL: independent builds produced different static archives' >&2
    exit 1
fi
printf 'PASS: two independent clean builds produced identical libtombstone.a (%s)\n' \
    "$(sha256sum "$TEMP_ROOT/a/libtombstone.a" | cut -d ' ' -f 1)"
