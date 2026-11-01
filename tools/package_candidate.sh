#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Reproducible source-only candidate; NEVER tags, signs, or publishes releases.
set -euo pipefail
export LC_ALL=C TZ=UTC
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="v0.1.0"
SOURCE_SHA="d6ae7d4016eb4efff6a684737711d809ec9d256f"
if [ "$#" -gt 0 ]; then OUT="$1"; else OUT="$ROOT/dist/$VERSION"; fi
ARCHIVE="TOMBSTONE-$VERSION-source.tar.gz"
PREFIX="TOMBSTONE-$VERSION/"
cd "$ROOT"

# Never silently package HEAD or unknown/modified worktree files.
actual="$(git rev-parse --verify "$SOURCE_SHA^{commit}")"
test "$actual" = "$SOURCE_SHA" || { echo "FAIL: source commit mismatch" >&2; exit 1; }
git merge-base --is-ancestor "$SOURCE_SHA" HEAD || {
  echo "FAIL: source SHA is not an ancestor of current checkout" >&2
  exit 1
}
test -r "release/$VERSION/POST_MERGE_EVIDENCE.md"
test -r "release/$VERSION/SOURCE_COMMIT.txt"
grep -Fq "$SOURCE_SHA" "release/$VERSION/SOURCE_COMMIT.txt"

# Avoid silently overwriting a previous candidate.
if [[ -e "$OUT" ]]; then
  echo "FAIL: destination already exists; choose a new empty output path" >&2
  exit 1
fi
mkdir -p "$OUT"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

git archive --format=tar "--prefix=$PREFIX" "$SOURCE_SHA" | gzip -n -9 > "$OUT/$ARCHIVE"
git archive --format=tar "--prefix=$PREFIX" "$SOURCE_SHA" | gzip -n -9 > "$tmp/$ARCHIVE"
cmp "$OUT/$ARCHIVE" "$tmp/$ARCHIVE" || {
  echo "FAIL: two archive builds differ" >&2
  exit 1
}

tar -tzf "$OUT/$ARCHIVE" > "$tmp/archive_paths.txt"
for path in \
  "${PREFIX}src/core/deletion.c" \
  "${PREFIX}src/crypto/fingerprint.c" \
  "${PREFIX}src/encoding/receipt.c" \
  "${PREFIX}apps/cli/src/main.rs" \
  "${PREFIX}apps/tui/src/main.rs" \
  "${PREFIX}apps/gtk/src/main.rs" \
  "${PREFIX}machine/examples/explicit-delete-v1.json"; do
  grep -Fxq "$path" "$tmp/archive_paths.txt" || {
    echo "FAIL: required source file missing from archive: $path" >&2

    exit 1
  }
done
cp "release/$VERSION/SOURCE_COMMIT.txt" "$OUT/SOURCE_COMMIT.txt"
cp "release/$VERSION/POST_MERGE_EVIDENCE.md" "$OUT/POST_MERGE_EVIDENCE.md"
(
  cd "$OUT"
  sha256sum "$ARCHIVE" SOURCE_COMMIT.txt POST_MERGE_EVIDENCE.md > SHA256SUMS.txt
  sha256sum --check --strict SHA256SUMS.txt
)
echo "SOURCE_COMMIT=$SOURCE_SHA"
echo "CANDIDATE_ASSETS=$OUT"
echo "ARCHIVE_REPRODUCIBILITY=PASS"
echo "CHECKSUM_VERIFICATION=PASS"
cat "$OUT/SHA256SUMS.txt"
