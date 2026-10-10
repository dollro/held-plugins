#!/usr/bin/env bash
# Deploy a stack (staging or production) from a caller (laptop or CI runner).
#
# The caller decrypts the secrets, resolves compose.deploy.yml and talks to the
# remote Docker daemon through a Docker context over SSH. The server holds no
# repo checkout, no decryption key and no env file on disk. The resolved values
# do live in the container config (visible to `docker inspect` on the host), so
# access to the host's Docker socket equals access to the secrets.
#
# Usage: DEPLOY_ENV=staging|production scripts/deploy.sh [--local] <verb> [args]
#   DEPLOY_ENV is required (no default); Task passes it from ENV=... .
# Registry credentials come from the caller's environment (REGISTRY_USER,
# REGISTRY_PASSWORD; CI secrets) or an existing `docker login`; they never go
# into the containers.
#   version   show the pinned APP_VERSION and the target
#   pull      log in to the registry and pull the pinned images
#   migrate   run Django migrations (and Alembic) as one-shot containers
#   up        start or update the stack
#   ps|logs   inspect the stack
#   backup    pg_dump into the postgres_backups volume
#   down      stop the stack
#   compose   pass the remaining arguments to docker compose
#
# Both environments run the same images and the same compose file; they differ
# only in .envs/<env>/ (secrets in app.env.enc, pinned version and host in
# deploy.env). A release is: pull -> migrate -> up, first on staging, then the
# same APP_VERSION on production. Rollback: revert the APP_VERSION bump in
# .envs/<env>/deploy.env and run the same three verbs.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd -P)"
DEPLOY_ENV="${DEPLOY_ENV:-}"
case "$DEPLOY_ENV" in staging|production) ;; *) echo "error: set DEPLOY_ENV=staging|production" >&2; exit 1 ;; esac
export DEPLOY_ENV  # compose.deploy.yml reads it (env files, router names)
ENV_DIR="$ROOT/.envs/$DEPLOY_ENV"
PROJECT="__PROJECT__-$DEPLOY_ENV"
# deploy.env feeds compose's own ${VAR} interpolation (image tag, host, network);
# compose parses it, the shell never evaluates it.
COMPOSE=(-f "$ROOT/compose.deploy.yml" -p "$PROJECT" --env-file "$ENV_DIR/deploy.env")
CONTEXT="${DEPLOY_CONTEXT:-$PROJECT}"
LOCAL=0

die() { echo "error: $*" >&2; exit 1; }
info() { echo "==> $*" >&2; }

[[ "${1:-}" == "--local" ]] && { LOCAL=1; shift; }
VERB="${1:-}"; [[ -n "$VERB" ]] || die "missing verb (see header of $0)"; shift

# Plaintext secrets exist on the caller only while this script runs, in a private
# temp file (never over a developer's decrypted .envs/<env>/app.env).
APP_ENV_FILE="$(mktemp)"
export APP_ENV_FILE  # compose.deploy.yml: env_file
cleanup() { rm -f "$APP_ENV_FILE"; }
trap cleanup EXIT

# Read one KEY=VALUE from a dotenv file literally. Never `source` env files:
# secrets contain $ ( ) & ; which the shell would execute or expand.
read_key() {
  local value
  value="$(grep -E "^$2=" "$1" | tail -n1 | cut -d= -f2-)" || true
  value="${value%\"}"; value="${value#\"}"; value="${value%\'}"; value="${value#\'}"
  printf '%s' "$value"
}

load_env() {
  ( umask 077
    sops --decrypt --input-type dotenv --output-type dotenv "$ENV_DIR/app.env.enc" \
      > "$APP_ENV_FILE" ) \
    || die "cannot decrypt $ENV_DIR/app.env.enc (age key in SOPS_AGE_KEY or ~/.config/sops/age/keys.txt?)"
  APP_VERSION="$(read_key "$ENV_DIR/deploy.env" APP_VERSION)"
  REGISTRY="$(read_key "$ENV_DIR/deploy.env" REGISTRY)"
  DEPLOY_SSH_TARGET="$(read_key "$ENV_DIR/deploy.env" DEPLOY_SSH_TARGET)"
  [[ -n "$APP_VERSION" && "$APP_VERSION" != "latest" ]] \
    || die "APP_VERSION must be pinned in .envs/$DEPLOY_ENV/deploy.env"
  [[ -n "$REGISTRY" ]] || die "REGISTRY missing in .envs/$DEPLOY_ENV/deploy.env"
}

ensure_context() {
  [[ "$LOCAL" == 1 ]] && { CONTEXT="$(docker context show)"; return; }
  [[ -n "${DEPLOY_SSH_TARGET:-}" ]] || die "DEPLOY_SSH_TARGET missing in deploy.env (ssh://user@host[:port])"
  local current
  current="$(docker context inspect "$CONTEXT" --format '{{.Endpoints.docker.Host}}' 2>/dev/null || true)"
  if [[ "$current" != "$DEPLOY_SSH_TARGET" ]]; then
    docker context rm -f "$CONTEXT" >/dev/null 2>&1 || true
    docker context create "$CONTEXT" --docker "host=$DEPLOY_SSH_TARGET" >/dev/null
    info "docker context $CONTEXT -> $DEPLOY_SSH_TARGET"
  fi
}

dc() { docker --context "$CONTEXT" compose "${COMPOSE[@]}" "$@"; }

load_env
ensure_context

case "$VERB" in
  version)
    echo "environment: $DEPLOY_ENV"; echo "app_version: $APP_VERSION"
    echo "registry:    $REGISTRY"; echo "context:     $CONTEXT"
    ;;
  pull)
    if [[ -n "${REGISTRY_USER:-}" ]]; then
      printf '%s' "${REGISTRY_PASSWORD:?REGISTRY_PASSWORD missing}" \
        | docker --context "$CONTEXT" login "${REGISTRY%%/*}" -u "$REGISTRY_USER" --password-stdin
    fi
    dc pull
    ;;
  migrate)
    dc up -d postgres redis
    # One-off containers must not receive traffic from the reverse proxy.
    dc run --rm --no-deps -l traefik.enable=false django python backend/manage.py migrate --noinput
    dc run --rm --no-deps -l traefik.enable=false django python backend/manage.py ensure_superuser
    # >>> realtime
    dc run --rm --no-deps -l traefik.enable=false realtime alembic -c realtime/alembic.ini upgrade head
    # <<< realtime
    ;;
  up)       dc up -d --remove-orphans --wait ;;
  down)     dc down ;;
  ps)       dc ps "$@" ;;
  logs)     dc logs -f --tail=200 "$@" ;;
  backup)
    dc exec postgres sh -c \
      'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > /backups/$(date +%Y%m%d-%H%M%S).dump'
    ;;
  compose)  dc "$@" ;;
  *)        die "unknown verb: $VERB" ;;
esac
