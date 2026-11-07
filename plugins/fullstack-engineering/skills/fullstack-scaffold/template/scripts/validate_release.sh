#!/usr/bin/env bash
# Guard a release tag before the long image build: fails in seconds on a wrong
# shape, a lightweight tag, or a version not newer than the newest release.
# Platform-neutral: CI passes the tag as VERSION (task release:validate VERSION=...).
# Needs the full tag history (CI: fetch tags, no shallow clone).
#
# Usage: scripts/validate_release.sh vX.Y.Z
set -euo pipefail

VERSION="${1:-}"
# CI checkouts may hold the tag only, or a lightweight copy of it: fetch the real tags.
git fetch --quiet --force --tags origin 2>/dev/null || true
die() { echo "error: $*" >&2; exit 1; }

[[ "$VERSION" =~ ^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]] \
  || die "release tags look like v1.2.3, got '$VERSION'"

git rev-parse -q --verify "refs/tags/$VERSION" >/dev/null || die "tag $VERSION does not exist"
[[ "$(git cat-file -t "refs/tags/$VERSION")" == "tag" ]] \
  || die "$VERSION is a lightweight tag; release tags are annotated (git tag -a $VERSION -m ...)"

# Annotated tags only: a stray lightweight tag is not a release.
newest="$(git for-each-ref --format='%(objecttype) %(refname:short)' 'refs/tags/v*' \
  | awk '$1 == "tag" { print $2 }' | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | grep -vx "$VERSION" | sort -V | tail -n1 || true)"
if [[ -n "$newest" ]]; then
  top="$(printf '%s\n%s\n' "$newest" "$VERSION" | sort -V | tail -n1)"
  [[ "$top" == "$VERSION" ]] || die "$VERSION is not newer than the newest release $newest"
fi
echo "release tag $VERSION ok${newest:+ (previous: $newest)}"
