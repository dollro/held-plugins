#!/bin/sh
# Pin a tool in scripts/ci/tools.txt to a new version: download it from the
# original source, hash it and rewrite its line. Review the release notes first.
# Usage: scripts/ci/pin-tool.sh <name> <version>   e.g. pin-tool.sh task v3.46.0
set -eu
. "$(dirname "$0")/tools-lib.sh"
[ $# -eq 2 ] || { echo "usage: $0 <name> <version>" >&2; exit 2; }
tool_fields "$1"
url="$(awk -v n="$1" '$1 == n { print $4; exit }' "$TOOLS_FILE" | sed "s/{version}/$2/g")"
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
curl -fsSL --retry 3 -o "$tmp" "$url"
sha="$(sha256_of "$tmp")"
awk -v n="$1" -v v="$2" -v s="$sha" '$1 == n { $2 = v; $3 = s } { print }' "$TOOLS_FILE" > "$tmp.txt"
mv "$tmp.txt" "$TOOLS_FILE"
echo "$1 $2 $sha"
