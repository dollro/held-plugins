#!/usr/bin/env bash
# Deploy a stack (staging or production) from a caller (CI job or laptop).
#
# The caller decrypts the secrets, resolves compose.deploy.yml and talks to the
# remote Docker daemon through a Docker context over SSH. The server holds no
# repo checkout, no decryption key and no env file on disk. The resolved values
# do live in the container config (visible to `docker inspect` on the host), so
# access to the host's Docker socket equals access to the secrets.
#
# Platform-neutral on purpose: CI files only set the variables below and call
# `task deploy`; nothing here knows whether it runs in GitHub, GitLab or a shell.
#
# Usage: DEPLOY_ENV=staging|production [APP_VERSION=__VERSION_EXAMPLE__] scripts/deploy.sh [--local] <verb> [args]
#   DEPLOY_ENV    required (no default); Task passes it from ENV=... .
#   APP_VERSION   the release to deploy (Task: VERSION=...; CI: the release tag).
#                 The images do not carry it: the containers get it from here and
#                 report it at /api/v1/version/, which verify compares.
#                 Required for preflight, pull, migrate, admin and up (never a default);
#                 preflight also takes a prerelease tag (read-only check);
#                 the other verbs default to the version that is running. For
#                 these four the checkout must be at that tag: compose.deploy.yml
#                 comes from the checkout and has to match the images.
#   ROLLBACK=1    allow a version older than the one running (deliberate rollback,
#                 logged). Laptop deploys pass it by hand. CI deploy jobs of a
#                 tag pipeline set it where the platform itself blocks outdated
#                 deploy jobs (GitLab), so re-running an older tag's deploy job
#                 is the rollback and needs no extra variable.
#   BACKUP_RETENTION_DAYS   dumps older than this are deleted (default 14)
#   REGISTRY_USER, REGISTRY_PASSWORD   pull credentials (never enter the containers)
#   RELEASE_REGISTRY   where the release pipeline pushed; preflight fails if it
#                 differs from REGISTRY in deploy.env
#   DEPLOY_SSH_KEY, DEPLOY_KNOWN_HOSTS   optional, for CI: a file path or the
#                 content itself; without them the caller's own SSH setup is used
#
# Verbs:
#   preflight  prove the deploy can work before changing anything: SSH login as
#              the deploy user, remote Docker, the proxy network, registry login, images present,
#              registry matches the release, version not older than the running one
#   backup     pg_dump into the postgres_backups volume (skipped on a first deploy)
#   pull       pull the images of APP_VERSION on the server
#   migrate    run Django migrations (and Alembic) as one-shot containers, then
#              the admin command (when DJANGO_SUPERUSER_EMAIL is set)
#   admin      only the admin command (ensure_admin), against the running version:
#              applies a changed DJANGO_SUPERUSER_PASSWORD without a release
#   up         start or update the stack and wait until healthy
#   verify     poll the public URL until /api/v1/health/ready/ is ok and
#              /api/v1/version/ reports APP_VERSION
#   version    show requested and running version and the target
#   manage     one-off Django management command in a one-shot container of the
#              running version, e.g. `task deploy:manage ENV=production -- shell`
#   ps|logs|down|compose   inspect or control the stack
#
# A release is: preflight -> backup -> pull -> migrate -> up -> verify
# (`task deploy ENV=... VERSION=...`), optionally first on staging, then the same
# version on production. Rollback: re-run the older tag's deploy job in CI, or from a laptop
# check out the previous tag and deploy it with ROLLBACK=1; migrations stay
# backward compatible for one release, so no restore is needed. The verify step
# after the deploy is the gate, not the version guard.
set -euo pipefail
set +x  # never trace: the values below include secrets

ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd -P)"
DEPLOY_ENV="${DEPLOY_ENV:-}"
[[ "${1:-}" == "--local" ]] && LOCAL_ARG=1 || LOCAL_ARG=0
# smoke: the production smoke test (scripts/smoke.sh) reuses migrate and up on
# the local daemon with its own generated, plaintext env file.
case "$DEPLOY_ENV" in
  staging|production) ;;
  smoke) [[ "$LOCAL_ARG" == 1 ]] || { echo "error: DEPLOY_ENV=smoke needs --local" >&2; exit 1; } ;;
  *) echo "error: set DEPLOY_ENV=staging|production" >&2; exit 1 ;;
esac
export DEPLOY_ENV  # compose.deploy.yml reads it (env files, router names)
ENV_DIR="$ROOT/.envs/$DEPLOY_ENV"
PROJECT="__PROJECT__-$DEPLOY_ENV"
CONTEXT="${DEPLOY_CONTEXT:-$PROJECT}"
LOCAL=0
# Compose opens SSH sessions in parallel; keep below sshd's MaxStartups/MaxSessions.
export COMPOSE_PARALLEL_LIMIT="${COMPOSE_PARALLEL_LIMIT:-4}"

die() { echo "error: $*" >&2; exit 1; }
info() { echo "==> $*" >&2; }

[[ "$LOCAL_ARG" == 1 ]] && { LOCAL=1; shift; }
VERB="${1:-}"; [[ -n "$VERB" ]] || die "missing verb (see header of $0)"; shift

# Plaintext secrets exist on the caller only while this script runs, in private
# temp files (never over a developer's decrypted .envs/<env>/app.env).
WORK="$(mktemp -d)"
APP_ENV_FILE="$WORK/app.env"
DEPLOY_ENV_FILE="$WORK/deploy.env"
export APP_ENV_FILE  # compose.deploy.yml: env_file
AGENT_PID=""
cleanup() {
  [[ -n "$AGENT_PID" ]] && kill "$AGENT_PID" 2>/dev/null || true
  rm -rf "$WORK"
}
trap cleanup EXIT

# Read one KEY=VALUE from a dotenv file literally. Never `source` env files:
# secrets contain $ ( ) & ; which the shell would execute or expand.
read_key() {
  local value
  value="$(grep -E "^$2=" "$1" | tail -n1 | cut -d= -f2-)" || true
  value="${value%$'\r'}"
  value="${value%\"}"; value="${value#\"}"; value="${value%\'}"; value="${value#\'}"
  printf '%s' "$value"
}

# A value that is either a path to a file or the content itself (CI platforms
# offer one or the other); prints a path.
as_file() {
  if [[ -f "$1" ]]; then printf '%s' "$1"; return; fi
  local file; file="$(mktemp -p "$WORK")"
  printf '%s\n' "$1" > "$file"; printf '%s' "$file"
}

load_env() {
  if [[ "$DEPLOY_ENV" == smoke ]]; then
    ( umask 077; tr -d '\r' < "$ENV_DIR/app.env" > "$APP_ENV_FILE" )
  else
  ( umask 077
    sops --decrypt --input-type dotenv --output-type dotenv "$ENV_DIR/app.env.enc" \
      | tr -d '\r' > "$APP_ENV_FILE" ) \
    || die "cannot decrypt $ENV_DIR/app.env.enc (age key in SOPS_AGE_KEY or ~/.config/sops/age/keys.txt?)"
  fi
  # Files edited on Windows carry CRLF; compose would keep the \r in every value.
  tr -d '\r' < "$ENV_DIR/deploy.env" > "$DEPLOY_ENV_FILE"
  REGISTRY="$(read_key "$DEPLOY_ENV_FILE" REGISTRY)"
  APP_HOST="$(read_key "$DEPLOY_ENV_FILE" APP_HOST)"
  DEPLOY_SSH_TARGET="$(read_key "$DEPLOY_ENV_FILE" DEPLOY_SSH_TARGET)"
  [[ -n "$REGISTRY" ]] || die "REGISTRY missing in .envs/$DEPLOY_ENV/deploy.env"
  [[ -n "$APP_HOST" ]] || die "APP_HOST missing in .envs/$DEPLOY_ENV/deploy.env"
}

setup_ssh() {
  [[ "$LOCAL" == 1 ]] && return
  if [[ -n "${DEPLOY_KNOWN_HOSTS:-}" ]]; then
    mkdir -p ~/.ssh && chmod 700 ~/.ssh
    cat "$(as_file "$DEPLOY_KNOWN_HOSTS")" >> ~/.ssh/known_hosts
  fi
  if [[ -n "${DEPLOY_SSH_KEY:-}" ]]; then
    start_agent
    # The key lives only in the agent, never in a file this script writes.
    if [[ -f "$DEPLOY_SSH_KEY" ]]; then
      ssh-add -q "$DEPLOY_SSH_KEY" || die "ssh-add refused the key in DEPLOY_SSH_KEY"
    else
      tr -d '\r' <<<"$DEPLOY_SSH_KEY" | ssh-add -q - || die "ssh-add refused the key in DEPLOY_SSH_KEY"
    fi
  fi
}

# A fresh agent of our own: an inherited SSH_AUTH_SOCK may point at a dead or
# foreign agent. Only ssh-agent's stdout is evaluated, and only after checking
# that it is what we expect (stderr would put messages into the eval).
start_agent() {
  unset SSH_AUTH_SOCK SSH_AGENT_PID
  local out
  out="$(ssh-agent -s 2>"$WORK/ssh-agent.err")" \
    || die "ssh-agent failed: $(cat "$WORK/ssh-agent.err")"
  [[ "$out" == *SSH_AUTH_SOCK=* ]] || die "unexpected ssh-agent output; not evaluating it"
  eval "$out" >/dev/null
  AGENT_PID="$SSH_AGENT_PID"
}

ensure_context() {
  [[ "$LOCAL" == 1 ]] && { CONTEXT="$(docker context show)"; return; }
  # The user is required: without it SSH falls back to the caller's user
  # (root in most CI containers) and fails on release day.
  [[ "$DEPLOY_SSH_TARGET" =~ ^ssh://[^@/]+@[^@/]+$ ]] \
    || die "DEPLOY_SSH_TARGET in .envs/$DEPLOY_ENV/deploy.env must be ssh://user@host[:port]"
  local current
  current="$(docker context inspect "$CONTEXT" --format '{{.Endpoints.docker.Host}}' 2>/dev/null || true)"
  if [[ "$current" != "$DEPLOY_SSH_TARGET" ]]; then
    docker context rm -f "$CONTEXT" >/dev/null 2>&1 || true
    docker context create "$CONTEXT" --docker "host=$DEPLOY_SSH_TARGET" >/dev/null
    info "docker context $CONTEXT -> $DEPLOY_SSH_TARGET"
  fi
}

remote() { docker --context "$CONTEXT" "$@"; }

running_version() {
  local image
  image="$(remote ps --filter "label=com.docker.compose.project=$PROJECT" \
    --filter "label=com.docker.compose.service=django" --format '{{.Image}}' | head -n1)"
  [[ -n "$image" ]] && printf '%s' "${image##*:}"
}

# Fails when APP_VERSION is older than the running version, unless ROLLBACK=1.
# Stops a stale deploy from overwriting a newer release by accident. Never
# refuses because the running version cannot be read: that happens exactly when
# production is broken and a rollback is needed; verify gates the result.
guard_version() {
  local running; running="$(running_version || true)"
  if [[ -z "$running" ]]; then
    info "warning: running version unknown in $DEPLOY_ENV (first deploy or stack down); not guarding"
    return
  fi
  [[ "$running" == "$APP_VERSION" ]] && return
  local newest; newest="$(printf '%s\n%s\n' "${running#v}" "${APP_VERSION#v}" | sort -V | tail -n1)"
  [[ "$newest" == "${APP_VERSION#v}" ]] && return
  [[ "${ROLLBACK:-0}" == 1 ]] \
    || die "$APP_VERSION is older than the running $running; set ROLLBACK=1 for a deliberate rollback"
  info "ROLLBACK: deploying $APP_VERSION over the running $running in $DEPLOY_ENV"
}

# compose.deploy.yml and the scripts come from this checkout, so it must be the
# commit the images were built from. Skipped with --local (deploy rehearsal).
require_checkout() {
  [[ "$LOCAL" == 1 ]] && return
  local tagged
  tagged="$(git -C "$ROOT" rev-parse -q --verify "refs/tags/$APP_VERSION^{commit}")" \
    || die "tag $APP_VERSION is not in this checkout (git fetch --tags)"
  [[ "$tagged" == "$(git -C "$ROOT" rev-parse HEAD)" ]] \
    || die "checkout is not at $APP_VERSION; deploy from that tag (git switch --detach $APP_VERSION)"
}

registry_login() {
  [[ -n "${REGISTRY_USER:-}" ]] || return 0
  printf '%s' "${REGISTRY_PASSWORD:?REGISTRY_PASSWORD missing}" \
    | docker "$@" login "${REGISTRY%%/*}" -u "$REGISTRY_USER" --password-stdin >/dev/null
}

# A release tag; with "prerelease" also a prerelease tag (preflight only).
require_version() {
  local kind
  kind="$("$ROOT/scripts/release.sh" shape "${APP_VERSION:-}")" \
    || die "APP_VERSION must be a release tag like __VERSION_EXAMPLE__ (task deploy ENV=... VERSION=...), got '${APP_VERSION:-}'"
  [[ "$kind" == release || "${1:-}" == prerelease ]] \
    || die "$APP_VERSION is a prerelease: only the read-only preflight runs for it"
}

# Admin account from the env (ensure_admin is idempotent; the env is the source
# of truth). Skipped when DJANGO_SUPERUSER_EMAIL is not set for this environment.
ensure_admin() {
  if [[ -z "$(read_key "$APP_ENV_FILE" DJANGO_SUPERUSER_EMAIL)" ]]; then
    info "DJANGO_SUPERUSER_EMAIL not set in $DEPLOY_ENV: admin command skipped"
    return
  fi
  one_off django python backend/manage.py ensure_admin
}

load_env
setup_ssh
ensure_context

case "$VERB" in
  preflight) require_version prerelease; require_checkout ;;
  # The smoke test deploys CI tags (tested-<sha>) or a local build: no release shape.
  migrate|up) [[ "$DEPLOY_ENV" == smoke ]] || { require_version; require_checkout; } ;;
  pull) require_version; require_checkout ;;
  *) APP_VERSION="${APP_VERSION:-$(running_version || true)}"
     APP_VERSION="${APP_VERSION:-none}" ;;
esac
export APP_VERSION  # compose.deploy.yml: image tags
# deploy.env feeds compose's own ${VAR} interpolation (host, network); compose
# parses it, the shell never evaluates it.
COMPOSE=(-f "$ROOT/compose.deploy.yml" -p "$PROJECT" --env-file "$DEPLOY_ENV_FILE")
dc() { remote compose "${COMPOSE[@]}" "$@"; }
# DEPLOY_PULL=never: images built locally (smoke test) are never pulled.
PULL=(); [[ -n "${DEPLOY_PULL:-}" ]] && PULL=(--pull "$DEPLOY_PULL")
# One-off containers must not receive traffic from the reverse proxy.
one_off() { dc run --rm --no-deps ${PULL[@]+"${PULL[@]}"} -l traefik.enable=false "$@"; }

images() {
  printf '%s\n' "$REGISTRY/__PROJECT__-django:$APP_VERSION"
  # >>> realtime
  printf '%s\n' "$REGISTRY/__PROJECT__-realtime:$APP_VERSION"
  # <<< realtime
}

case "$VERB" in
  preflight)
    info "ssh login and remote docker ($DEPLOY_SSH_TARGET)"
    remote version --format 'server docker {{.Server.Version}}' \
      || die "cannot reach the Docker daemon over SSH: check the deploy user, its key and its docker group"
    # The shared Traefik owns this network; without it `up` fails late, and a
    # router whose middleware is missing answers 404 (check proxy logs after).
    proxy_net="$(read_key "$DEPLOY_ENV_FILE" PROXY_NETWORK)"
    remote network inspect "${proxy_net:-proxy}" >/dev/null 2>&1 \
      || die "network ${proxy_net:-proxy} missing on the server: start the shared Traefik first (docs/operations.md)"
    lower() { printf '%s' "${1%/}" | tr '[:upper:]' '[:lower:]'; }  # bash 3 (macOS) safe
    if [[ -n "${RELEASE_REGISTRY:-}" && "$(lower "$RELEASE_REGISTRY")" != "$(lower "$REGISTRY")" ]]; then
      die "release pushed to $RELEASE_REGISTRY but $DEPLOY_ENV pulls from $REGISTRY"
    fi
    info "registry login on the server and on the caller"
    registry_login --context "$CONTEXT" || die "the server cannot log in to ${REGISTRY%%/*}"
    registry_login || die "cannot log in to ${REGISTRY%%/*}"
    while read -r image; do
      # imagetools names the real error (auth, not found); `docker manifest
      # inspect` says "no such manifest" for every failure.
      err="$(docker buildx imagetools inspect "$image" 2>&1 >/dev/null)" \
        || die "image not available: $image (${err:-no details})"
      info "found $image"
    done < <(images)
    guard_version
    info "preflight ok: $DEPLOY_ENV can deploy $APP_VERSION"
    ;;
  version)
    echo "environment: $DEPLOY_ENV"; echo "requested:   ${APP_VERSION}"
    echo "running:     $(running_version || echo none)"
    echo "registry:    $REGISTRY"; echo "context:     $CONTEXT"
    ;;
  backup)
    if [[ -z "$(dc ps -q postgres 2>/dev/null)" ]]; then
      info "no running database (first deploy): nothing to back up"
    else
      # Temp file, renamed only on success: a failed dump never looks like a
      # good backup. Dumps hold personal data (deleted users too): rotate them.
      dc exec -T -e RETENTION="${BACKUP_RETENTION_DAYS:-14}" postgres sh -c '
        set -e; name=$(date +%Y%m%d-%H%M%S).dump; tmp=/backups/.$name.tmp
        trap "rm -f \"$tmp\"" EXIT
        pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$tmp"
        mv "$tmp" "/backups/$name"
        find /backups -name "*.dump" -mtime +"$RETENTION" -delete'
      info "backup written to the postgres_backups volume (off-host copies: scheduled backup)"
    fi
    ;;
  pull)
    guard_version
    registry_login --context "$CONTEXT"
    dc pull
    ;;
  migrate)
    dc up -d postgres redis
    one_off django python backend/manage.py migrate --noinput
    # >>> realtime
    one_off realtime alembic -c realtime/alembic.ini upgrade head
    # <<< realtime
    ensure_admin
    ;;
  admin)
    # The running version only: a one-off container of another version could
    # meet a schema it does not know.
    running="$(running_version || true)"
    [[ -n "$running" ]] || die "nothing running in $DEPLOY_ENV"
    [[ "$running" == "$APP_VERSION" ]] \
      || die "$DEPLOY_ENV runs $running, not $APP_VERSION; run the admin job of the running release"
    ensure_admin
    ;;
  up)
    guard_version
    info "docker compose $(docker compose version --short) (the smoke test should use the same)"
    dc up -d ${PULL[@]+"${PULL[@]}"} --remove-orphans --wait
    ;;
  manage)
    [[ "$APP_VERSION" != none ]] || die "nothing running in $DEPLOY_ENV"
    one_off django python backend/manage.py "$@"
    ;;
  verify)
    url="https://$APP_HOST"
    for attempt in $(seq 1 "${VERIFY_ATTEMPTS:-24}"); do
      body="$(curl -fsS --max-time 10 "$url/api/v1/version/" 2>/dev/null || true)"
      if [[ "$body" == *"\"version\":\"$APP_VERSION\""* ]] \
         && curl -fsS --max-time 10 -o /dev/null "$url/api/v1/health/ready/"; then
        echo "deployed: $url runs $APP_VERSION and is ready"; exit 0
      fi
      info "attempt $attempt: not yet serving $APP_VERSION (${body:-no answer})"; sleep 5
    done
    die "$url does not serve $APP_VERSION"
    ;;
  down)     dc down ;;
  ps)       dc ps "$@" ;;
  logs)     dc logs -f --tail=200 "$@" ;;
  compose)  dc "$@" ;;
  *)        die "unknown verb: $VERB" ;;
esac
