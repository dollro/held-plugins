#!/usr/bin/env bash
# End-to-end in a CI job without Docker-in-Docker (task test:e2e STACK=job).
# The app runs as job services from the commit's images, by digest: django and
# celeryworker (django image), realtime, Postgres, Redis (and the mail catcher).
# They never read the checkout, so the "services start before the checkout"
# race cannot hit them. This container (the official Playwright image) runs
# the proxy from the checkout's Caddyfile and the checkout's specs, through the
# proxy like production routing. Needs caddy on PATH (scripts/ci/tools.txt).
#
# Usage: scripts/e2e_job.sh [playwright args]
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd -P)"
cd "$ROOT"
info() { echo "==> $*" >&2; }

caddy run --config docker/proxy/Caddyfile --adapter caddyfile >caddy.log 2>&1 &
CADDY_PID=$!
trap 'kill "$CADDY_PID" 2>/dev/null || true' EXIT

# The services migrate and seed on start: wait for their readiness, not just a port.
wait_ready() {
  info "waiting for $1"
  node -e '
    const url = process.argv[1], until = Date.now() + 300_000;
    (async () => {
      while (Date.now() < until) {
        try { if ((await fetch(url)).ok) return; } catch {}
        await new Promise((r) => setTimeout(r, 2000));
      }
      console.error(`not ready after 300 s: ${url}`); process.exit(1);
    })();' "$1"
}
wait_ready "http://django:5000/api/v1/health/ready/"
# >>> realtime
wait_ready "http://realtime:8001/health/ready"
# <<< realtime
wait_ready "http://localhost:8080/api/v1/health/ready/"

info "playwright against the proxy (http://localhost:8080)"
APP_DIR="$ROOT" E2E_BASE_URL=http://localhost:8080 docker/frontend/pnpm run test:e2e "$@"
