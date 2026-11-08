# Shared by install-tools.sh, mirror-tools.sh and pin-tool.sh (sourced, POSIX sh).
#
# Pinned tools come from scripts/ci/tools.txt. In CI (CI=true, set by every
# common platform) a download tries the mirror first, then the original source;
# outside CI only the original source is used. The SHA-256 is checked either way.
#
# Mirror: any HTTP store that serves GET and accepts PUT at
#   $TOOL_MIRROR_URL/<name>/<version without v>/<file>
# (a generic package registry, Nexus raw, Artifactory, an S3-compatible bucket
# behind a gateway). TOOL_MIRROR_HEADER is one optional request header for
# auth, e.g. "JOB-TOKEN: <token>" or "Authorization: Bearer <token>".
# Unset TOOL_MIRROR_URL: original source only.

TOOLS_FILE="$(dirname "$0")/tools.txt"

# tool_fields <name>: sets VERSION, SHA256, URL, FILE; fails if unknown.
tool_fields() {
  line="$(awk -v n="$1" '$1 == n { print; exit }' "$TOOLS_FILE")"
  [ -n "$line" ] || { echo "unknown tool: $1 (not in $TOOLS_FILE)" >&2; return 1; }
  set -- $line
  VERSION="$2" SHA256="$3"
  URL="$(printf '%s' "$4" | sed "s/{version}/$VERSION/g")"
  FILE="${URL##*/}"
}

sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
  else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

mirror_url() { printf '%s/%s/%s/%s' "${TOOL_MIRROR_URL%/}" "$1" "${VERSION#v}" "$FILE"; }

# curl_mirror <curl args...>: curl with the optional auth header, never echoed.
curl_mirror() {
  if [ -n "${TOOL_MIRROR_HEADER:-}" ]; then curl -H "$TOOL_MIRROR_HEADER" "$@"
  else curl "$@"; fi
}

# verify <name> <file> <source>: check the pinned SHA-256 (tool_fields first).
verify() {
  actual="$(sha256_of "$2")"
  if [ "$actual" != "$SHA256" ]; then
    echo "$1 $VERSION from $3: SHA-256 $actual, expected $SHA256" >&2
    rm -f "$2"; return 1
  fi
  echo "$1 $VERSION from $3, SHA-256 verified" >&2
}

# fetch_upstream <name> <out>: original source only, verified.
fetch_upstream() {
  tool_fields "$1" || return 1
  curl -fsSL --retry 3 --retry-all-errors -o "$2" "$URL" || {
    echo "$1 $VERSION: download failed: $URL" >&2; return 1; }
  verify "$1" "$2" "$URL"
}

# fetch <name> <out>: in CI the mirror first, then the original source; verified.
fetch() {
  tool_fields "$1" || return 1
  # A missing or wrong mirror copy falls back to the original source.
  if [ "${CI:-}" = "true" ] && [ -n "${TOOL_MIRROR_URL:-}" ] \
     && curl_mirror -fsSL --retry 2 -o "$2" "$(mirror_url "$1")" 2>/dev/null \
     && verify "$1" "$2" mirror; then
    return 0
  fi
  fetch_upstream "$1" "$2"
}
