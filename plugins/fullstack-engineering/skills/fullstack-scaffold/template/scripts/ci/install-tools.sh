#!/bin/sh
# CI setup only: install pinned tools from scripts/ci/tools.txt on any runner
# image (Alpine docker:cli, Debian, Ubuntu), mirror first in CI, hash checked.
# Usage: scripts/ci/install-tools.sh task [sops] [docker-compose]
set -eu
. "$(dirname "$0")/tools-lib.sh"
BIN="${BIN:-/usr/local/bin}"
PLUGINS="${DOCKER_CONFIG:-$HOME/.docker}/cli-plugins"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
for tool in "$@"; do
  fetch "$tool" "$tmp/$tool.download"
  case "$FILE" in
    *.tar.gz) tar -xzf "$tmp/$tool.download" -C "$tmp" "$tool" && src="$tmp/$tool" ;;
    *) src="$tmp/$tool.download" ;;
  esac
  case "$tool" in
    docker-*) mkdir -p "$PLUGINS" && dest="$PLUGINS/$tool" ;;  # Docker CLI plugin
    *) dest="$BIN/$tool" ;;
  esac
  chmod 0755 "$src"
  if [ -w "$(dirname "$dest")" ]; then mv -f "$src" "$dest"; else sudo mv -f "$src" "$dest"; fi
done
