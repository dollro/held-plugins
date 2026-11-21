#!/bin/sh
# Build once, promote the tested digest. CI builds every commit once as
# <base>-<service>:<sha> plus the test image <base>-django:test-<sha>; the test
# jobs run exactly the digests the build recorded, and `mark` tags exactly those
# tested-<sha>. A release never rebuilds: it copies tested-<sha> to the version.
# Tags are never trusted: two pipelines building the same SHA push different
# digests under the same :<sha> (builds are not bit-reproducible).
#
#   tested_images.sh record METADATA OUT   bake --metadata-file -> dotenv OUT (DIGEST_*)
#   tested_images.sh reuse OUT             commit tested already: OUT with the tested
#                                          digests, exit 0; else exit 3 (build)
#   tested_images.sh check-image REF DIGEST
#                                          REF (the job's image) is pinned to DIGEST
#   tested_images.sh ran OUT               after a passing test job: the DIGEST_* it ran
#   tested_images.sh mark RAN...           <image>@DIGEST_* -> tested-<sha> (test image:
#                                          test-tested-<sha>), only if every RAN file
#                                          names exactly these digests; pins the cache
#   tested_images.sh await SECONDS OUT     wait for tested-<sha> of every service;
#                                          dotenv OUT: TESTED=true, or TESTED=false
#                                          after SECONDS (the tag pipeline rebuilds)
#   tested_images.sh promote VERSION       tested-<sha> -> VERSION, digest checked
#   tested_images.sh record-cache OUT      append the digests of the cache refs this
#                                          build wrote (CACHE_*) to OUT
#   tested_images.sh restore-cache REF     cache-tested-<sha>-* -> cache-REF-*
#
# Build cache: a pipeline that reuses a tested commit builds nothing and so never
# writes its branch's cache; an integration branch fast-forwarded to tested
# commits would go stale and every new branch would build cold. So `mark` pins
# the cache the tested build wrote as cache-tested-<sha>-<stage>, and the reuse
# path on an integration branch copies it to cache-<ref>-<stage>. A missing cache
# only makes a later build slower: every cache step logs and goes on.
#
# Environment: IMAGE_BASE (<registry>/<path>/<project>), COMMIT (the full SHA),
# CACHE_REF (branch slug, for record-cache), REGCTL (default: regctl on PATH),
# AWAIT_INTERVAL (default 30 s). With REGISTRY_HOST, REGISTRY_USER and
# REGISTRY_PASSWORD set, regctl logs in first; otherwise it uses existing
# credentials. POSIX sh: runs in Alpine job images and the test image alike.
set -eu

REGCTL="${REGCTL:-regctl}"
# Released services. The bake targets of the `ci` group carry the same names.
SERVICES="django"
# >>> realtime
SERVICES="$SERVICES realtime"
# <<< realtime
# Recorded and marked, never promoted: the test image of the same build.
RECORDED="$SERVICES django-test"
# Cache refs of one build as <repository>:<stage> (cache_to in docker-bake.hcl).
CACHES="django:django django:test"
# >>> realtime
CACHES="$CACHES realtime:realtime"
# <<< realtime

base() { echo "${IMAGE_BASE:?IMAGE_BASE is not set}"; }
commit() { echo "${COMMIT:?COMMIT is not set}"; }

# django-test -> DIGEST_DJANGO_TEST
digest_var() { echo "DIGEST_$(echo "$1" | tr 'a-z-' 'A-Z_')"; }
# django-test lives in the django repository.
repo() { echo "$(base)-${1%-test}"; }
tested_tag() {
  case "$1" in
    *-test) echo "test-tested-$(commit)" ;;
    *) echo "tested-$(commit)" ;;
  esac
}
is_digest() { printf '%s' "$1" | grep -Eqx 'sha256:[0-9a-f]{64}'; }
env_value() { eval "printf '%s' \"\${$1:-}\""; }

login() {
  [ -n "${REGISTRY_PASSWORD:-}" ] || return 0
  printf '%s' "$REGISTRY_PASSWORD" |
    "$REGCTL" registry login "${REGISTRY_HOST:?}" -u "${REGISTRY_USER:?}" --pass-stdin >/dev/null
}

# bake's metadata file: one top-level object per target (2-space indent), with
# containerimage.digest at 4 spaces for every pushed image.
record() {
  metadata="$1" out="$2"
  : >"$out.part"
  for name in $RECORDED; do
    digest="$(awk -v t="$name" '
      /^  "[^"]+": \{/ { split($0, a, "\""); cur = a[2] }
      cur == t && /^    "containerimage.digest": "/ { split($0, a, "\""); print a[4]; exit }
    ' "$metadata")"
    if ! is_digest "$digest"; then
      echo "$metadata: no image digest for $name" >&2
      rm -f "$out.part"; exit 1
    fi
    echo "$(digest_var "$name")=$digest" >>"$out.part"
  done
  mv "$out.part" "$out"
  cat "$out"
}

reuse() {
  out="$1"
  : >"$out.part"
  for name in $RECORDED; do
    tags="$("$REGCTL" tag ls "$(repo "$name")" 2>/dev/null)" || tags=""
    if ! printf '%s\n' "$tags" | grep -qx "$(tested_tag "$name")"; then
      echo "No $(repo "$name"):$(tested_tag "$name"): build"
      rm -f "$out.part"; return 3
    fi
    echo "$(digest_var "$name")=$("$REGCTL" image digest "$(repo "$name"):$(tested_tag "$name")")" >>"$out.part"
  done
  mv "$out.part" "$out"
  echo "$(commit) is tested already: reusing its images"
  cat "$out"
}

check_image() {
  ref="$1" digest="$2"
  is_digest "$digest" || { echo "No recorded digest ('$digest'): the build's dotenv report is missing" >&2; exit 1; }
  case "$ref" in
    *"@$digest") echo "Running $ref" ;;
    *) echo "$ref is not the recorded $digest" >&2; exit 1 ;;
  esac
}

# Copy src (tag or @digest) to dst and check the digest.
copy_checked() {
  src="$1" dst="$2" want="$3"
  "$REGCTL" image copy "$src" "$dst"
  got="$("$REGCTL" image digest "$dst")"
  [ "$got" = "$want" ] || { echo "$dst is $got, not $want" >&2; exit 1; }
  echo "$src -> $dst"
}

# The DIGEST_* of this job's environment, validated, as dotenv lines.
digest_lines() {
  for name in $RECORDED; do
    var="$(digest_var "$name")" digest="$(env_value "$(digest_var "$name")")"
    is_digest "$digest" || { echo "No recorded digest for $name ($var)" >&2; return 1; }
    echo "$var=$digest"
  done
}

ran() {
  out="$1"
  digest_lines >"$out.part" || { rm -f "$out.part"; exit 1; }
  mv "$out.part" "$out"
  echo "Tests passed on:"; cat "$out"
}

# GitLab retries a job without its dependents: after a retried build, the mark
# job gets new digests although a test job passed on the old ones. Every RAN
# file must name exactly the digests to mark.
mark() {
  [ "$#" -gt 0 ] || { echo "usage: $0 mark RAN..." >&2; exit 2; }
  expected="$(digest_lines)" || exit 1
  for ran_file in "$@"; do
    [ -s "$ran_file" ] || { echo "$ran_file is missing: no proof a test job passed on these digests" >&2; exit 1; }
    if [ "$(cat "$ran_file")" != "$expected" ]; then
      echo "$ran_file names other digests than the build recorded (retried build?):" >&2
      echo "--- $ran_file" >&2; cat "$ran_file" >&2
      echo "--- recorded" >&2; echo "$expected" >&2
      exit 1
    fi
  done
  for name in $RECORDED; do
    digest="$(env_value "$(digest_var "$name")")"
    copy_checked "$(repo "$name")@$digest" "$(repo "$name"):$(tested_tag "$name")" "$digest"
  done
  pin_cache
}

# Services without tested-<sha>; fails when the registry cannot be read, so an
# auth error or an outage does not count as "not tested yet".
missing_tested() {
  for service in $SERVICES; do
    tags="$("$REGCTL" tag ls "$(base)-$service")" || return 1
    printf '%s\n' "$tags" | grep -qx "tested-$(commit)" || printf '%s ' "$service"
  done
}

await() {
  timeout="$1" out="$2" interval="${AWAIT_INTERVAL:-30}"
  start="$(date +%s)" errors=0
  echo "Waiting up to ${timeout}s for tested-$(commit) ($SERVICES)"
  while :; do
    if missing="$(missing_tested)"; then
      errors=0
      [ -n "$missing" ] || { echo "tested-$(commit) found for every service"; echo "TESTED=true" >"$out"; return 0; }
    else
      errors=$((errors + 1))
      echo "Registry read failed ($errors/3)" >&2
      [ "$errors" -lt 3 ] || exit 1
      missing="(unknown)"
    fi
    elapsed=$(($(date +%s) - start))
    if [ "$elapsed" -ge "$timeout" ]; then
      echo "No tested-$(commit) after ${elapsed}s (missing: $missing): build and test it first"
      echo "TESTED=false" >"$out"; return 0
    fi
    echo "${elapsed}s: missing tested-$(commit) for $missing"
    sleep "$interval"
  done
}

promote() {
  version="$1"
  missing="$(missing_tested)" || { echo "Registry read failed" >&2; exit 1; }
  [ -z "$missing" ] || { echo "No tested-$(commit) for: $missing" >&2; exit 1; }
  for service in $SERVICES; do
    src="$(base)-$service:tested-$(commit)"
    copy_checked "$src" "$(base)-$service:$version" "$("$REGCTL" image digest "$src")"
  done
}

# <repository>:<stage> -> CACHE_<REPOSITORY>_<STAGE>, repository, tag.
cache_var() { echo "CACHE_$(echo "${1%%:*}_${1#*:}" | tr 'a-z-' 'A-Z_')"; }
cache_repo() { echo "$(base)-${1%%:*}"; }
cache_tag() { echo "cache-$2-${1#*:}"; }

# Read right after the bake (the metadata file does not name the cache). An
# overlapping pipeline of the same branch may have replaced the ref since; the
# pin then names that build's cache: still warm, never wrong.
record_cache() {
  out="$1" ref="${CACHE_REF:-}"
  [ -n "$ref" ] || { echo "CACHE_REF not set: cache not recorded"; return 0; }
  login || { echo "Registry login failed: cache not recorded"; return 0; }
  for cache in $CACHES; do
    src="$(cache_repo "$cache"):$(cache_tag "$cache" "$ref")"
    if digest="$("$REGCTL" image digest "$src" 2>/dev/null)" && is_digest "$digest"; then
      echo "$(cache_var "$cache")=$digest" | tee -a "$out"
    else
      echo "No cache $src: not recorded (a later build is slower)"
    fi
  done
}

# Part of mark: never fails it.
pin_cache() {
  for cache in $CACHES; do
    digest="$(env_value "$(cache_var "$cache")")"
    dst="$(cache_repo "$cache"):$(cache_tag "$cache" "tested-$(commit)")"
    if ! is_digest "$digest"; then
      echo "No recorded $(cache_var "$cache"): $dst not pinned"
    elif "$REGCTL" image copy "$(cache_repo "$cache")@$digest" "$dst"; then
      echo "Cache pinned: $dst"
    else
      echo "Cache $(cache_repo "$cache")@$digest is gone: $dst not pinned"
    fi
  done
}

restore_cache() {
  ref="$1"
  for cache in $CACHES; do
    src="$(cache_repo "$cache"):$(cache_tag "$cache" "tested-$(commit)")"
    dst="$(cache_repo "$cache"):$(cache_tag "$cache" "$ref")"
    if "$REGCTL" image copy "$src" "$dst" 2>/dev/null; then
      echo "Cache $src -> $dst"
    else
      echo "No cache $src: $dst stays as it is (the next build is slower)"
    fi
  done
}

usage() {
  echo "usage: $0 record METADATA OUT | reuse OUT | check-image REF DIGEST | ran OUT |" \
    "mark RAN... | await SECONDS OUT | promote VERSION | record-cache OUT | restore-cache REF" >&2
  exit 2
}

cmd="${1:-}"; [ "$#" -gt 0 ] && shift
case "$cmd" in
  record) [ "$#" -eq 2 ] || usage; record "$1" "$2" ;;
  reuse) [ "$#" -eq 1 ] || usage; login; reuse "$1" || exit $? ;;
  check-image) [ "$#" -eq 2 ] || usage; check_image "$1" "$2" ;;
  ran) [ "$#" -eq 1 ] || usage; ran "$1" ;;
  mark) login; mark "$@" ;;
  await) [ "$#" -eq 2 ] || usage; login; await "$1" "$2" ;;
  promote) [ "$#" -eq 1 ] || usage; login; promote "$1" ;;
  record-cache) [ "$#" -eq 1 ] || usage; record_cache "$1" ;;
  restore-cache) [ "$#" -eq 1 ] || usage; login || true; restore_cache "$1" ;;
  *) usage ;;
esac
