#!/usr/bin/env bash
# Production smoke test: the production images, the production settings and
# compose.deploy.yml behind a throwaway Traefik, on the local Docker daemon.
# Catches what tests on development images miss (static files missing from the
# image, 500 instead of 404 with DEBUG off, dead account pages, a missing user
# or group in the image, hosts or secure-cookie settings).
#
# Usage (Task: task release:smoke [REGISTRY=... VERSION=...]):
#   scripts/smoke.sh                         build the images locally, then test
#   REGISTRY=r VERSION=v1.2.3 scripts/smoke.sh   test the pushed release images
#   SMOKE_DUMP=path/to/prod.dump ...       restore a production backup (pg_dump -Fc)
#                 first, so the release's migrations run against real data. Only
#                 where production data may be (never as a CI artifact).
# Run it with the same Docker and Compose versions as the deploy job (CI: the
# same job image), or a Compose difference shows up only on release day.
# Platform-neutral: runs the same on a laptop, a GitHub runner or GitLab
# Docker-in-Docker (all checks run inside containers on the smoke network).
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd -P)"
cd "$ROOT"
export DEPLOY_ENV=smoke
PROJECT="__PROJECT__-smoke"
NETWORK="$PROJECT-proxy"
TRAEFIK="$PROJECT-traefik"
HOST="smoke.localhost"
DIR="$ROOT/.envs/smoke"   # gitignored, removed on exit
export APP_ENV_FILE="$DIR/app.env"

die() { echo "error: $*" >&2; exit 1; }
info() { echo "==> $*" >&2; }
rand() { head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n'; }

if [[ -n "${VERSION:-}" ]]; then
  REGISTRY="${REGISTRY:?REGISTRY is required with VERSION}"
  export APP_VERSION="$VERSION" PULL=missing
else
  REGISTRY="smoke.local" APP_VERSION="smoke"; export APP_VERSION PULL=never
fi

dc() { docker compose -f compose.deploy.yml -p "$PROJECT" --env-file "$DIR/deploy.env" "$@"; }

cleanup() {
  status=$?
  if [[ $status -ne 0 && -f "$DIR/deploy.env" ]]; then
    dc logs --tail=80 >&2 || true
  fi
  dc down -v --remove-orphans >/dev/null 2>&1 || true
  docker rm -f "$TRAEFIK" >/dev/null 2>&1 || true
  docker network rm "$NETWORK" >/dev/null 2>&1 || true
  rm -rf "$DIR"
  exit $status
}
trap cleanup EXIT

# ── Images ──────────────────────────────────────────────────────────────────
if [[ "$PULL" == never ]]; then
  info "building production images locally"
  REGISTRY="$REGISTRY" IMAGETAG="$APP_VERSION" PLATFORMS="${PLATFORMS:-linux/amd64}" \
    docker buildx bake --set '*.output=type=docker' --set '*.cache-from=' --set '*.cache-to='
elif [[ -n "${REGISTRY_USER:-}" ]]; then
  printf '%s' "${REGISTRY_PASSWORD:?REGISTRY_PASSWORD missing}" \
    | docker login "${REGISTRY%%/*}" -u "$REGISTRY_USER" --password-stdin >/dev/null
fi

# ── Env: production example with generated throwaway secrets ───────────────
mkdir -p "$DIR"
db_user="$(grep -E '^POSTGRES_USER=' .envs/production/app.env.example | cut -d= -f2-)"
db_name="$(grep -E '^POSTGRES_DB=' .envs/production/app.env.example | cut -d= -f2-)"
db_pass="$(rand)"
overrides="$(cat <<EOF
APP_ENVIRONMENT=smoke
DJANGO_SECRET_KEY=$(rand)$(rand)
DJANGO_ALLOWED_HOSTS=$HOST
DJANGO_CSRF_TRUSTED_ORIGINS=https://$HOST
DJANGO_ADMIN_URL=smoke-admin/
DJANGO_SUPERUSER_EMAIL=smoke@example.com
DJANGO_SUPERUSER_PASSWORD=$(rand)
POSTGRES_PASSWORD=$db_pass
DATABASE_URL=postgres://$db_user:$db_pass@postgres:5432/$db_name
EMAIL_URL=smtp://localhost:25
INTERNAL_API_SECRET=$(rand)
EOF
)"
( umask 077
  grep -v -E "^($(printf '%s\n' "$overrides" | cut -d= -f1 | paste -sd'|'))=" \
    .envs/production/app.env.example > "$APP_ENV_FILE"
  printf '%s\n' "$overrides" >> "$APP_ENV_FILE" )
cat > "$DIR/deploy.env" <<EOF
APP_HOST=$HOST
REGISTRY=$REGISTRY
PROXY_NETWORK=$NETWORK
TLS_CERTRESOLVER=none
EOF

# ── Throwaway Traefik (default self-signed certificate) ────────────────────
docker network create "$NETWORK" >/dev/null
sock="${DOCKER_HOST:-unix:///var/run/docker.sock}"
[[ "$sock" == unix://* ]] && sock="${sock#unix://}" || sock=/var/run/docker.sock
docker run -d --name "$TRAEFIK" --network "$NETWORK" \
  -v "$sock:/var/run/docker.sock:ro" "traefik:__TRAEFIK_VERSION__" \
  --providers.docker.exposedByDefault=false --providers.docker.network="$NETWORK" \
  --entryPoints.websecure.address=:443 >/dev/null

# ── Deploy sequence as in scripts/deploy.sh ─────────────────────────────────
info "starting the stack ($APP_VERSION) with $(docker compose version --short 2>/dev/null || echo '?') compose"
dc pull --quiet postgres redis
[[ "$PULL" == missing ]] && dc pull --quiet
dc up -d --pull never --wait postgres redis
if [[ -n "${SMOKE_DUMP:-}" ]]; then
  [[ -f "$SMOKE_DUMP" ]] || die "SMOKE_DUMP not found: $SMOKE_DUMP"
  info "restoring $SMOKE_DUMP, then migrating on top of it"
  dc exec -T postgres sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl --exit-on-error' \
    < "$SMOKE_DUMP"
fi
run() { dc run --rm --no-deps --pull never -l traefik.enable=false "$@"; }
run django python backend/manage.py migrate --noinput
run django python backend/manage.py ensure_superuser
# >>> realtime
run realtime alembic -c realtime/alembic.ini upgrade head
# <<< realtime
dc up -d --pull never --remove-orphans --wait

# ── Checks, from a container on the smoke network ──────────────────────────
info "checking https://$HOST through Traefik"
docker run --rm -i --network "$NETWORK" --entrypoint python \
  -e SMOKE_HOST="$HOST" -e SMOKE_PROXY="$TRAEFIK" -e SMOKE_VERSION="$APP_VERSION" \
  -e SMOKE_ADMIN=smoke-admin/ \
  "$REGISTRY/__PROJECT__-django:$APP_VERSION" - < scripts/smoke_checks.py
info "smoke test passed"
