#!/usr/bin/env bash
# Set up and tear down Docker Sandboxes (sbx) for Claude Code on a repo,
# a git worktree or a private clone. Non-interactive: it prepares and checks
# the sandbox; the human attaches with the printed `sbx run --name` line.
#
#   sandbox.sh preflight
#   sandbox.sh create [--branch <type>/<name>] [--base <branch>] [--path <dir>]
#                     [--kit <dir>] [--clone] [--recreate]
#                     [--stack [--docker-size 40g] [--memory 12g]]
#   sandbox.sh check  <sandbox-name>
#   sandbox.sh done   <sandbox-name> [--force]
#
# Output lines start with OK, WARN, FAIL, INFO or ATTACH. Exit codes:
# 0 ok, 1 usage/error, 2 preflight failed, 3 no kit found.
set -uo pipefail

ok()   { echo "OK    $*"; }
warn() { echo "WARN  $*"; }
fail() { echo "FAIL  $*"; }
info() { echo "INFO  $*"; }
die()  { fail "$*"; exit 1; }

sbx_exists() { sbx ls -q 2>/dev/null | grep -qx "$1"; }
sbx_workspace() {  # first (primary) workspace of a sandbox
  sbx ls --json 2>/dev/null | python3 -c 'import json,sys
n=sys.argv[1]
for b in json.load(sys.stdin).get("sandboxes",[]):
    if b["name"]==n and b.get("workspaces"): print(b["workspaces"][0])' "$1"
}

main_root() {
  local common
  common=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || return 1
  dirname "$common"
}

find_kit() {
  local root=$1 kits
  mapfile -t kits < <(find "$root/.sbx" -mindepth 2 -maxdepth 2 -name spec.yaml 2>/dev/null | sort)
  [ "${#kits[@]}" -eq 1 ] && dirname "${kits[0]}" && return 0
  [ "${#kits[@]}" -gt 1 ] && { fail "several kits under $root/.sbx; pass --kit"; return 1; }
  return 1
}

kit_env() {  # prints KEY=VALUE for environment.variables of a v2 kit
  awk '
    /^environment:/ {env=1; next}
    env && /^[^ #]/ {env=0}
    env && /^  variables:/ {vars=1; next}
    env && vars && /^  [^ ]/ {vars=0}
    env && vars && /^    [A-Za-z_][A-Za-z0-9_]*:/ {
      line=$0; sub(/^    /,"",line); key=line; sub(/:.*/,"",key)
      val=line; sub(/^[^:]*:[ ]*/,"",val); sub(/[ ]+#.*$/,"",val); gsub(/^"|"$/,"",val)
      print key "=" val
    }' "$1/spec.yaml"
}

default_base() {
  if git show-ref -q --verify refs/heads/develop || git show-ref -q --verify refs/remotes/origin/develop; then
    echo develop
  else
    git symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || git branch --show-current
  fi
}

cmd_preflight() {
  local rc=0
  if ! command -v sbx >/dev/null; then
    fail "sbx not installed: https://github.com/docker/sbx-releases/releases (Linux: sudo apt install ./DockerSandboxes-linux-<arch>-<build>.deb)"
    exit 2
  fi
  ok "sbx $(sbx version 2>/dev/null | awk '{print $3}')"
  if sbx daemon status 2>/dev/null | grep -qi 'running'; then ok "daemon running"
  else fail "daemon not running: sbx daemon start -d"; rc=2; fi
  if [ $rc -eq 0 ]; then
    if sbx ls >/dev/null 2>&1; then ok "signed in"
    else fail "not signed in: run 'sbx login' in a terminal and confirm the code in the browser"; rc=2; fi
  fi
  git rev-parse --show-toplevel >/dev/null 2>&1 || { fail "not inside a git repository"; rc=2; }
  exit $rc
}

cmd_create() {
  local branch="" base="" path="" kit="" clone=0 recreate=0 stack=0 dsize=40g mem=12g
  while [ $# -gt 0 ]; do
    case $1 in
      --branch) branch=$2; shift 2 ;;
      --base) base=$2; shift 2 ;;
      --path) path=$2; shift 2 ;;
      --kit) kit=$2; shift 2 ;;
      --clone) clone=1; shift ;;
      --recreate) recreate=1; shift ;;
      --stack) stack=1; shift ;;
      --docker-size) dsize=$2; shift 2 ;;
      --memory) mem=$2; shift 2 ;;
      *) die "unknown option $1" ;;
    esac
  done

  local root; root=$(main_root) || die "not inside a git repository"
  if [ -z "$kit" ]; then
    kit=$(find_kit "$root") || { fail "no sandbox kit (.sbx/<name>/spec.yaml) in $root"; exit 3; }
  fi
  kit=$(cd "$kit" && pwd)
  sbx kit validate "$kit" >/dev/null 2>&1 && ok "kit $kit" || die "kit invalid: sbx kit validate $kit"

  local repo; repo=$(basename "$root")
  local ws extra=() name
  if [ $clone -eq 1 ]; then
    ws=$root
    name="claude-${repo}-clone"
  else
    if [ -n "$branch" ]; then
      local short=${branch##*/}
      ws="$(dirname "$root")/${repo}-${short}"
      [ -e "$ws" ] && die "$ws already exists; use --path $ws to sandbox it"
      if git -C "$root" show-ref -q --verify "refs/heads/$branch"; then
        git -C "$root" worktree add -q "$ws" "$branch" || die "git worktree add failed"
        ok "worktree $ws on existing branch $branch"
      else
        base=${base:-$(cd "$root" && default_base)}
        git -C "$root" worktree add -q -b "$branch" "$ws" "$base" || die "git worktree add failed"
        ok "worktree $ws on new branch $branch from $base"
      fi
    else
      ws=${path:-$(git rev-parse --show-toplevel)}
      ws=$(cd "$ws" && pwd)
    fi
    name="claude-$(basename "$ws")"
    if [ -f "$ws/.git" ]; then
      extra=("$root/.git")
      info "linked worktree: mounting $root/.git as a second, writable workspace"
    fi
  fi
  name=$(echo "$name" | tr -c 'A-Za-z0-9.\n-' '-')

  if sbx_exists "$name"; then
    if [ $recreate -eq 1 ]; then
      sbx rm -f "$name" >/dev/null 2>&1 && ok "removed old sandbox $name"
    else
      warn "sandbox $name already exists (kit and mounts are fixed at creation); pass --recreate to rebuild it"
      echo "ATTACH: sbx run --name $name"
      exit 0
    fi
  fi

  local sizing=() envsz=()
  if [ $stack -eq 1 ]; then
    # Sizes are fixed at creation; the default 10 GB Docker disk is too small for a full stack.
    sizing=(-m "$mem")
    envsz=(DOCKER_SANDBOXES_DOCKER_SIZE="$dsize" DOCKER_SANDBOXES_ROOT_SIZE=30g)
    info "stack mode: Docker disk $dsize, memory $mem"
  fi
  info "creating sandbox $name (first creation runs the kit's install steps; can take minutes)"
  if [ $clone -eq 1 ]; then
    env "${envsz[@]}" sbx create --name "$name" "${sizing[@]}" --clone claude --kit "$kit" "$ws" >/dev/null || die "sbx create failed"
  else
    env "${envsz[@]}" sbx create --name "$name" "${sizing[@]}" claude --kit "$kit" "$ws" "${extra[@]}" >/dev/null || die "sbx create failed"
  fi
  ok "sandbox $name created"
  if [ $stack -eq 1 ]; then
    local df; df=$(sbx exec "$name" sh -c "df -h /var/lib/docker | awk 'NR==2{print \$2}'" </dev/null 2>/dev/null | tail -1)
    ok "docker disk in sandbox: ${df:-unknown}"
    local ov; ov=$(cd "$ws" && git ls-files | grep -E '(^|/)(compose|local|docker-compose)[^/]*\.sbx\.ya?ml$' | head -1)
    if [ -n "$ov" ]; then ok "compose overlay for the sandbox: $ov"
    else warn "no compose overlay (*.sbx.yml): containers inside will not reach external services; see agent-sandbox.md, Stack inside the sandbox"; fi
  fi
  KIT=$kit WS=$ws cmd_check "$name"
}

cmd_check() {
  local name=${1:?sandbox name}
  sbx_exists "$name" || die "no sandbox $name"
  local ws=${WS:-$(sbx_workspace "$name")}   # clone mode: the private clone sits at the same path

  local out
  out=$(sbx exec "$name" sh -c "cd '$ws' && git status -sb 2>&1 | head -1" </dev/null 2>&1 | tail -1)
  case $out in
    "##"*) ok "git in sandbox: $out" ;;
    *) fail "git in sandbox: $out" ;;
  esac

  local kit=${KIT:-}
  if [ -z "$kit" ]; then
    local root; root=$(cd "$ws" 2>/dev/null && main_root) || root=""
    [ -n "$root" ] && kit=$(find_kit "$root" 2>/dev/null) || true
  fi
  if [ -n "$kit" ]; then
    while IFS='=' read -r key val; do
      [ -z "$key" ] && continue
      got=$(sbx exec "$name" printenv "$key" </dev/null 2>/dev/null | tail -1)
      if [ "$got" = "$val" ]; then ok "env $key"; else warn "env $key is '$got', kit says '$val' (sandbox older than the kit? --recreate)"; fi
      if [[ $val =~ host\.docker\.internal:([0-9]+) ]]; then
        port=${BASH_REMATCH[1]}
        # The sandbox proxy answers 500 itself when the host port has no listener
        # (policy log: "forward ... dial failed") and 403 when policy blocks it.
        resp=$(sbx exec "$name" sh -c "curl -s -m 5 -w '\\n%{http_code}' '$val'" </dev/null 2>/dev/null)
        code=$(printf '%s' "$resp" | tail -1)
        if printf '%s' "$resp" | grep -qiE 'dial|connection refused|no such host' || [ "$code" = "000" ] || [ -z "$code" ]; then
          warn "host service $val not reachable: nothing listening on the host's localhost:$port (start the service on the host)"
        elif [ "$code" = "403" ] && printf '%s' "$resp" | grep -qiE 'approval|policy|blocked|denied'; then
          warn "host service $val blocked by policy: add localhost:$port to the kit's allow list or run: sbx policy allow network localhost:$port"
        else ok "host service $val reachable (HTTP $code)"; fi
      fi
    done < <(kit_env "$kit")
  fi
  echo "ATTACH: sbx run --name $name"
}

cmd_done() {
  local name=${1:?sandbox name} force=0
  [ "${2:-}" = "--force" ] && force=1
  sbx_exists "$name" || die "no sandbox $name"
  local ws; ws=$(sbx_workspace "$name")
  local is_wt=0
  [ -f "$ws/.git" ] && is_wt=1
  if [ $is_wt -eq 1 ] && [ $force -eq 0 ]; then
    if [ -n "$(git -C "$ws" status --porcelain)" ]; then die "$ws has uncommitted changes; commit or pass --force"; fi
    local up ahead
    up=$(git -C "$ws" rev-parse --abbrev-ref '@{upstream}' 2>/dev/null) || die "$(git -C "$ws" branch --show-current) has no upstream (not pushed); push or pass --force"
    ahead=$(git -C "$ws" rev-list --count "$up..HEAD")
    [ "$ahead" -gt 0 ] && die "$ahead commit(s) not pushed to $up; push or pass --force"
  fi
  if [ $is_wt -eq 0 ] && [ $force -eq 0 ] && git -C "$ws" remote get-url "sandbox-$name" >/dev/null 2>&1; then
    die "clone-mode sandbox: removing it deletes the sandbox-$name remote and any work not yet taken over. First: git fetch sandbox-$name, then branch or merge from sandbox-$name/<branch>; then done --force"
  fi
  sbx rm -f "$name" >/dev/null 2>&1 && ok "removed sandbox $name"
  if [ $is_wt -eq 1 ]; then
    local root branch
    root=$(cd "$ws" && main_root)
    branch=$(git -C "$ws" branch --show-current)
    if [ $force -eq 1 ]; then git -C "$root" worktree remove --force "$ws"; else git -C "$root" worktree remove "$ws"; fi \
      && ok "removed worktree $ws"
    if git -C "$root" branch -d "$branch" >/dev/null 2>&1; then ok "deleted merged branch $branch"
    else info "kept branch $branch (not merged locally)"; fi
  else
    info "workspace $ws is not a linked worktree; left in place"
  fi
}

case "${1:-}" in
  preflight) shift; cmd_preflight "$@" ;;
  create) shift; cmd_create "$@" ;;
  check) shift; cmd_check "$@" ;;
  done) shift; cmd_done "$@" ;;
  *) sed -n '2,13p' "$0"; exit 1 ;;
esac
