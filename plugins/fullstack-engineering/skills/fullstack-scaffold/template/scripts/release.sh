#!/usr/bin/env bash
# Release tags: shape, order and notes. The version is the release tag and
# nothing else (no version file, no bump commit). Platform-neutral: CI passes the
# version as an argument; needs the tag history (CI: full clone, tags fetched).
#
# Shape of this project (one shape, never mixed; sorting and protected tag
# patterns depend on it):
#   release      1.8   (^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))?$)
#   prerelease   (^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))?-?(a|b|rc)[0-9]+$): runs the tag pipeline up to the read-only
#                preflight, never deploys
#
# Usage:
#   scripts/release.sh shape VERSION       print "release" or "prerelease", fail otherwise
#   scripts/release.sh validate VERSION    tag pipeline: shape, annotated, a release is
#                                          newer than the newest other release; a
#                                          prerelease only with ALLOW_PRERELEASE=1 (a
#                                          pipeline that stops before deploying)
#   scripts/release.sh prepare VERSION COMMIT
#                                          before creating a release on COMMIT: shape,
#                                          tag not taken, newer than the newest release,
#                                          COMMIT contains it; writes release-notes.md
#   scripts/release.sh newest              the newest release tag (empty if none)
set -euo pipefail

RELEASE_RE='^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))?$'
PRERELEASE_RE='^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))?-?(a|b|rc)[0-9]+$'

die() { echo "error: $*" >&2; exit 1; }

shape() {
  if [[ "$1" =~ $RELEASE_RE ]]; then echo release
  elif [[ "$1" =~ $PRERELEASE_RE ]]; then echo prerelease
  else return 1; fi
}

fetch_tags() {
  # CI checkouts may hold the tag only, or a lightweight copy of it.
  git fetch --quiet --force --tags origin 2>/dev/null || true
}

# Annotated release tags only, oldest first; a stray lightweight tag is no release.
releases() {
  git for-each-ref --format='%(objecttype) %(refname:short)' refs/tags \
    | awk '$1 == "tag" { print $2 }' | { grep -E "$RELEASE_RE" || true; } | sort -V
}

newest_except() { releases | { grep -vxF "$1" || true; } | tail -n1; }

is_newer() {  # is_newer A B: A sorts after B
  [[ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | tail -n1)" == "$1" && "$1" != "$2" ]]
}

require_shape() {
  shape "$1" >/dev/null \
    || die "'$1' is not a release (like 1.8) or prerelease tag of this project"
}

validate() {
  local version="$1" kind newest
  require_shape "$version"; kind="$(shape "$version")"
  [[ "$kind" == release || "${ALLOW_PRERELEASE:-0}" == 1 ]] \
    || die "$version is a prerelease; this pipeline deploys releases only"
  fetch_tags
  git rev-parse -q --verify "refs/tags/$version" >/dev/null || die "tag $version does not exist"
  [[ "$(git cat-file -t "refs/tags/$version")" == tag ]] \
    || die "$version is a lightweight tag; release tags are annotated (git tag -a $version -m ...)"
  newest="$(newest_except "$version")"
  if [[ "$kind" == release && -n "$newest" ]] && ! is_newer "$version" "$newest"; then
    die "$version is not newer than the newest release $newest"
  fi
  echo "$kind tag $version ok${newest:+ (newest release before it: $newest)}"
}

prepare() {
  local version="$1" commit="$2" kind newest
  require_shape "$version"; kind="$(shape "$version")"
  fetch_tags
  ! git rev-parse -q --verify "refs/tags/$version" >/dev/null || die "tag $version exists already"
  newest="$(newest_except "$version")"
  if [[ -n "$newest" ]]; then
    if [[ "$kind" == release ]] && ! is_newer "$version" "$newest"; then
      die "$version is not newer than the newest release $newest"
    fi
    # The job stays playable in older pipelines: releasing a commit without the
    # newest release would roll production back.
    git merge-base --is-ancestor "$newest" "$commit" \
      || die "$commit does not contain release $newest; release from a newer pipeline"
  fi
  {
    echo "Changes since ${newest:-the first commit}:"
    echo
    git log --no-merges --format='- %s (%h)' ${newest:+"$newest.."}"$commit"
  } > release-notes.md
  cat release-notes.md
  echo "ready to tag $commit as $version ($kind)"
}

case "${1:-}" in
  shape) shape "${2:?usage: $0 shape VERSION}" ;;
  validate) validate "${2:?usage: $0 validate VERSION}" ;;
  prepare) prepare "${2:?usage: $0 prepare VERSION COMMIT}" "${3:?usage: $0 prepare VERSION COMMIT}" ;;
  newest) fetch_tags; releases | tail -n1 ;;
  *) echo "usage: $0 shape|validate|prepare|newest ..." >&2; exit 2 ;;
esac
