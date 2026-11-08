#!/bin/sh
# Mirror every pinned tool in scripts/ci/tools.txt that the mirror lacks:
# download from the original source, verify the SHA-256, upload with PUT.
# Runs in CI on protected refs only (it writes), allowed to fail. A version
# bump is mirrored by the first pipeline on a protected ref after it, provided
# the original source is reachable then. Needs TOOL_MIRROR_URL (see tools-lib.sh).
set -eu
. "$(dirname "$0")/tools-lib.sh"
[ -n "${TOOL_MIRROR_URL:-}" ] || { echo "TOOL_MIRROR_URL not set: nothing to mirror" >&2; exit 0; }
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
failed=0
for tool in $(awk '!/^#/ && NF { print $1 }' "$TOOLS_FILE"); do
  tool_fields "$tool"
  if curl_mirror -fsSL -o /dev/null -r 0-0 "$(mirror_url "$tool")" 2>/dev/null; then
    echo "$tool $VERSION: already mirrored"; continue
  fi
  if fetch_upstream "$tool" "$tmp/$FILE" \
     && curl_mirror -fsS --upload-file "$tmp/$FILE" "$(mirror_url "$tool")" >/dev/null; then
    echo "$tool $VERSION: mirrored"
  else
    echo "$tool $VERSION: not mirrored" >&2; failed=1
  fi
done
exit "$failed"
