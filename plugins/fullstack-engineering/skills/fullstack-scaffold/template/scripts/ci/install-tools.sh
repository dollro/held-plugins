#!/bin/sh
# CI setup only: install the tools Task targets need, on any runner image
# (Alpine docker:cli, Debian, GitHub ubuntu). Usage: scripts/ci/install-tools.sh [task] [sops]
set -eu
SOPS_VERSION="${SOPS_VERSION:-v3.10.2}"
BIN="${BIN:-/usr/local/bin}"
for tool in "${@:-task}"; do
  if command -v "$tool" >/dev/null 2>&1; then continue; fi
  case "$tool" in
    task) sh -c "$(curl -fsSL https://taskfile.dev/install.sh)" -- -d -b "$BIN" ;;
    sops)
      curl -fsSLo "$BIN/sops" \
        "https://github.com/getsops/sops/releases/download/$SOPS_VERSION/sops-$SOPS_VERSION.linux.amd64"
      chmod +x "$BIN/sops" ;;
    *) echo "unknown tool: $tool" >&2; exit 1 ;;
  esac
done
