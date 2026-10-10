# Agent sandboxes

How to develop with coding agents inside a sandbox without fighting permissions, the network policy or the local stack. Checked in October 2026 against Docker Sandboxes (`sbx`) 0.47 and Claude Code's sandboxing docs; sources in `sources.md`. Both move fast and `sbx kit`/`sbx env` are marked experimental: check flags with `sbx <command> --help` and the docs before writing them into a repo.

A sandbox limits what an autonomous agent can reach: files, network, credentials. Pick the kind first, because the rules for Docker and host access differ:

| Kind | Isolation | Docker inside | Reaching a host service |
|-|-|-|-|
| **Docker Sandboxes** (`sbx`) | microVM per sandbox; workspace shared at the same path through virtiofs | Yes, a private Docker engine per sandbox; the host engine is unreachable | `http://host.docker.internal:<port>`, allowed as `localhost:<port>` |
| **Claude Code native sandbox** (`/sandbox`) | bubblewrap (Linux) or Seatbelt (macOS) around shell commands only; file tools, MCP servers and hooks run outside it | No; `docker` is incompatible with it | Linux: `127.0.0.1:<port>` in `sandbox.network.allowedDomains`; macOS: `allowLocalBinding` |
| **Dev container** (e.g. the Claude Code reference container) | Container with a default-deny firewall script | Not without the host socket (see below) | `host.docker.internal:<port>` plus a firewall rule |

**Never give a sandbox the host's Docker socket.** `/var/run/docker.sock` is root-equivalent on the host and a documented escape route out of agent sandboxes. Where an agent must run containers, use a sandbox with its own engine (`sbx`), never a mounted socket.

## Install and start `sbx`

- **Linux:** download the `.deb` from https://github.com/docker/sbx-releases/releases. Pick the build whose Ubuntu release is closest to the host's glibc (`ldd --version`): the newest build for Debian testing/sid and current Ubuntu, the older one for older LTS hosts. Install with `sudo apt install ./DockerSandboxes-linux-amd64-<build>.deb`; the package is `docker-sbx` and upgrades in place.
- **macOS / Windows:** use the installer from the same releases page or the Docker docs.
- **Start:** `sbx daemon start -d` (without `-d` it runs in the foreground), check with `sbx daemon status`, then `sbx login`. Upgrading: `sbx daemon stop`, install the new package, start again; `sbx version` confirms.

## Where the dev stack runs

Two places, chosen by who needs the stack:

| Stack | Use it when | The agent can |
|-|-|-|
| **Inside the sandbox** (`sbx` only; its own Docker engine) | The agent should verify its own work: build, start, run integration tests, fix, repeat | Run everything itself, including tests that need the database or the full stack |
| **On the host** | The human works in the browser against the stack, or the sandbox kind cannot run Docker | Edit, lint, type-check, run unit tests; call the host stack over HTTP for API and end-to-end checks; hand stack commands (migrations, integration tests) to the human |

Anthropic's core advice for agents is a check they can run themselves, so the loop closes without a human in it. With the stack on the host, every integration test goes through the human. Prefer the stack inside the sandbox for agent work; keep a host stack for browser work. The Claude Code native sandbox cannot run Docker at all (its escape hatch `sandbox.excludedCommands` runs commands without any limit); there the host stack is the only choice.

### Stack inside the sandbox

Measured on a Django + FastAPI + Celery + Postgres + Redis + Vite stack (sbx 0.47, 16 CPUs): cold build of 7 images 162 s, `up --wait` 34–54 s, backend suite of 428 tests ~40 s. Images took ~13 GB of Docker disk, the running stack ~4 GB RAM.

- **Size the sandbox at creation.** The Docker disk defaults to 10 GB, too small for such a stack. `DOCKER_SANDBOXES_DOCKER_SIZE=40g DOCKER_SANDBOXES_ROOT_SIZE=30g sbx create … -m 12g …` (sizes cannot change later; `/sandbox --stack` does this).
- **Images are per sandbox.** Sandboxes do not share images or layers; each new sandbox builds once, then keeps its images until `sbx rm`.
- **Containers do not inherit the sandbox's proxy or CA.** Image builds went through in the test, but running containers could not reach external services, not even DNS (`No address associated with hostname`). Add a compose overlay used only inside the sandbox:

  ```yaml
  # compose.sbx.yml: docker compose -f compose.local.yml -f compose.sbx.yml up -d --wait
  x-sbx-proxy: &sbx-proxy
    HTTP_PROXY: http://gateway.docker.internal:3128
    HTTPS_PROXY: http://gateway.docker.internal:3128
    http_proxy: http://gateway.docker.internal:3128
    https_proxy: http://gateway.docker.internal:3128
    # service names direct; host.docker.internal goes through the proxy to the real host
    NO_PROXY: localhost,127.0.0.1,::1,django,realtime,postgres,redis,worker
    no_proxy: localhost,127.0.0.1,::1,django,realtime,postgres,redis,worker
    SSL_CERT_FILE: /sbx-ca/ca-certificates.crt
    REQUESTS_CA_BUNDLE: /sbx-ca/ca-certificates.crt
    NODE_EXTRA_CA_CERTS: /sbx-ca/ca-certificates.crt
  x-sbx-ca: &sbx-ca
    - /etc/ssl/certs/ca-certificates.crt:/sbx-ca/ca-certificates.crt:ro   # system CAs + proxy CA
  services:
    django:  { environment: *sbx-proxy, volumes: *sbx-ca }
    realtime: { environment: *sbx-proxy, volumes: *sbx-ca }
    worker:  { environment: *sbx-proxy, volumes: *sbx-ca }
  ```

  The proxy address and bundle path are what the sandbox itself uses (`env | grep -i proxy` inside it). Check them when sbx changes.
- **External APIs the stack calls go into the kit's allow list** (speech-to-text, LLM providers); otherwise they fail with HTTP 403 `Approval required`.
- **Gitignored files a new worktree lacks** (decrypted env files) must be copied in before `up`; they then sit inside the sandbox where the agent can read them.
- **Ports stay inside the sandbox.** Parallel sandboxes each run their own stack on the same ports without colliding; publish one to the host only to look at it (`sbx ports <name> --publish <host>:<port>`; services listen on `0.0.0.0`).
- **Ownership is fine.** A container running as root inside the sandbox writes files that appear on the host owned by the host user (tested on a host with UID 1000, the same as the agent user's; rerun `touch` from a container and `ls -ln` on the host when the UIDs differ).
- **Startup order shows up here first.** A clean stack in a fresh sandbox exposes races a long-lived host stack hides, such as a scheduler starting before migrations; use `depends_on: … condition: service_healthy`.

### Stack on the host

- The workspace is shared, so the host stack's dev servers (Django runserver, uvicorn `--reload`, Vite) pick up the agent's edits immediately.
- The agent reaches host services as in the kinds table above. Make the URL configurable with a localhost default so the same config works on both sides: `${ATLAS_API_URL:-http://localhost:8000}`, set to the sandbox value in the sandbox environment.
- When a check needs the stack (migrations, integration tests, a rebuild), the agent says which host command to run and why, then continues with the result.
- Containers started by the host's Docker write into a bind-mounted repo as their image user, often root (File ownership).
- If you allow `docker compose` through the native sandbox's `excludedCommands`, keep the pattern narrow and the command on an ask rule: the agent can edit the compose file it then runs.

The repo's CLAUDE.md says which stack the agent uses, the commands for it, and the URLs of host services.

## File ownership

**One UID writes into the repo.** The host user, the sandbox's agent user (1000 in `sbx`) and every container that writes into a bind mount use the same UID/GID.

**Pass the real IDs explicitly.** Compose interpolates only from exported environment variables and `.env`. Bash's `UID` is not exported and `GID` is usually not set, so `user: "${UID:-1000}:${GID:-1000}"` silently falls back to 1000. Export both from the Taskfile:

```yaml
# Taskfile.yml
env:
  UID: { sh: id -u }
  GID: { sh: id -g }
```

```yaml
# compose.local.yml, on every service that writes into the mount
user: "${UID}:${GID}"
environment:
  HOME: /tmp            # an unknown UID has no home; npm, pnpm and uv need a writable cache
```

Or let `task setup` write `UID=` and `GID=` into an untracked `.env`. For plain `docker compose` without Task, export them in the shell: `export UID GID; GID=$(id -g)`. Bash refuses `UID=…` because `UID` is read-only, but it can export it.

| Source of foreign-owned files | Example | Fix |
|-|-|-|
| Compose service without a user | A Node/Vite service writes `.pnpm-store/`, `.vite/`, `dist/` as root | `user:` as above |
| Dependencies in the mount | `node_modules`, `.venv` and the pnpm store inside the repo | `node_modules` in a named volume; venv outside the mount (anonymous volume on `/app/.venv`, or `UV_PROJECT_ENVIRONMENT=/opt/venv`); pnpm store in a volume |
| Same environment used on both sides | A `.venv` created in the sandbox, then used on the host | Each side builds its own. A venv records absolute interpreter paths and symlinks and does not move between machines (uv's Docker guide says the same). In the kit: `UV_PROJECT_ENVIRONMENT: "/home/agent/<repo>-venv"` |
| App runtime state in the workspace | Local databases, ledgers or sync tokens under `state/` written by the app on both sides | Point the app's state setting outside the workspace in the kit environment (e.g. `STATE_DIR: "/home/agent/<repo>-state"`); the host keeps its own |
| MCP servers on both sides | A code-index or browser MCP writes repo-local state (`.serena/`, `.playwright-mcp/`) from the sandbox and again from the host | Run each such server on one side, or move its state out of the repo (MCP section) |
| Install steps as root | A kit install command writes into `$HOME` or the repo as root (root is the install default in `sbx` kits) | `user: "1000"` for anything that writes outside system paths |
| Worktrees | A worktree inherits the compose setup and its root-owned output | Same fixes; check worktrees when hunting stray files |

Alternatives, where they fit: dev containers fix the UID automatically on Linux (`updateRemoteUserUID`, on by default); rootless Podman maps your UID with `--userns=keep-id`; Docker Desktop for Linux maps IDs through its VirtioFS share. Plain Docker Engine on Linux has no idmapped bind mounts, so the `user:` fix stays. Compose `develop.watch` syncs host to container only, so container writes never reach the host; files the container must produce for the repo (lockfiles, migrations) then need `docker compose cp` or a bind mount.

Find and repair on the host:

```bash
find . -xdev ! -user "$(id -u)" -not -path '*/node_modules/*' -printf '%u %p\n' | head
docker run --rm -v "$PWD":/w alpine chown -R "$(id -u):$(id -g)" /w/<path>   # no sudo needed
```

**Changing the store path or the container user breaks existing dependency volumes.** A `node_modules` volume created by root, or linked to the old pnpm store, makes pnpm refuse to start. `docker compose up -d --build -V` (`--renew-anon-volumes`) replaces anonymous volumes such as `node_modules` and keeps named ones such as the database. For a named dependency volume, remove just that one (`docker volume rm <project>_<volume>`). Never `docker compose down -v` for this: it deletes the database volumes too.

**Set a moved pnpm store once for the whole image,** not per command: `ENV npm_config_store_dir=/pnpm-store` in the Dockerfile, and the same BuildKit cache mount on every `RUN` that calls pnpm. Indirect calls run pnpm without your flags (`npx browserslist --update-db` runs `pnpm up`) and fail when the store moved.

**A service that must run as its own user** cannot take `--user <host uid>` (e.g. a database dump that locks the data directory owned by the service user). Run it as before and hand the output back at the end: `sh -c '<dump> && chown -R <uid>:<gid> /export'`.

Repair is the fallback. Fix the compose file or the kit that produced the files, or they come back.

## Shared workspace or clone (`sbx`)

- **Shared workspace** (default): the sandbox works on the host checkout. Use it for the inner loop: agent edits, host stack hot-reloads, human looks at the result.
- **Clone mode** (`sbx run --clone`, chosen at creation): the host repo is mounted read-only and the agent works on a private clone. Fetch its work with `git fetch sandbox-<name>` while the sandbox runs; `sbx rm` removes that remote. No ownership collisions, and the stack can run inside the sandbox without touching your checkout. Use it for parallel agents and for tasks that should not touch the working copy.
- `sbx run --rm` removes the sandbox when the session ends.

### A git worktree in a sandbox

The `/sandbox` skill does all of this (worktree, mounts, kit, checks) and prints the line to attach; what follows is what it does and why.

A linked worktree has no repository of its own: its `.git` is a one-line file (`gitdir: <main repo>/.git/worktrees/<name>`). Mount the main repo's `.git` as a second, writable workspace; sbx mounts every workspace at its host path, so the pointer resolves. Run it from the main checkout so the kit is the current one, not an older copy on the worktree's branch:

```bash
cd ~/src/atlas
sbx run claude --kit ./.sbx/atlas ../atlas-feature ./.git
```

- Without the `.git` mount every git command fails with `fatal: not a git repository: …/.git/worktrees/<name>`. The mount cannot be `:ro`, because commits write objects and refs into the main `.git`. It also gives the agent every branch and the other worktrees' metadata.
- The sandbox is named after the first workspace (`claude-atlas-feature`); re-attach with `sbx run --name <name>`.
- **Host stack from a worktree is not a second stack.** Compose names the project after the directory of the compose file, which is the same in every checkout, so `up` in the worktree takes over the main checkout's containers and database volume. For a separate stack use `docker compose -p <repo>-<branch> …` and other host ports; otherwise run one stack at a time.
- **Alternative: clone mode** for independent tasks: `sbx run claude --clone --kit ./.sbx/atlas` from the main checkout. Other branches are available in the clone as `origin/<branch>`; the host fetches the agent's commits with `git fetch sandbox-<name>`. No writable `.git` mount and no checkout to collide with, but the host stack only sees the work after the fetch.

## Network policy

Proxy-based allowlists decide on the hostname. In `sbx` the default is the Balanced preset: deny, plus a baseline allowlist.

- **Keep the repo's rules in its kit** (`permissions.network.allow` in a v2 kit), so every sandbox for the repo starts with the same rules. Group them: toolchain (`astral.sh`, `pypi.org`, `files.pythonhosted.org`, `registry.npmjs.org`, `github.com`, `codeload.github.com`, `objects.githubusercontent.com`), the git host, MCP endpoints, model and API providers that tests call.
- **Host services:** `sbx policy allow network localhost:<port>` (global, or `--sandbox <name>`); the agent calls `host.docker.internal:<port>`. A `localhost:<port>` entry in the kit's allow list is registered as the same rule (it shows up under the kit in `sbx policy ls`), so keep it in the kit.
- **A wildcard does not match the bare domain:** `*.example.com` does not allow `example.com`. List both.
- **Failing integration tests are a policy question first.** Connection refused, timeouts or TLS errors on an external call: read `sbx policy log` before touching code; `sbx policy check` tests a single request. Try a fix with `sbx policy allow network`, then move it into the kit.
- **Broad entries are exfiltration paths.** `github.com`, `*.googleapis.com` or a paste site let an agent send data out; the proxy does not inspect TLS, so domain fronting can slip past it. Allow what the work needs, narrow with deny rules (`sbx policy deny`, `sandbox.network.deniedDomains`).
- **Credentials at the proxy, not in the sandbox.** `sbx secret` service secrets reach the agent only as a sentinel (`proxy-managed`) and the proxy injects the real value; `sbx secret set-custom` does the same for other tokens through an `sbx-cs-*` placeholder. The native sandbox can mask variables with `sandbox.credentials`.

## MCP servers and secrets

- **Committed `.mcp.json` holds placeholders only.** Claude Code expands `${VAR}` and `${VAR:-default}` in `command`, `args`, `env`, `url` and `headers`; an unset variable without a default stays as literal text. Example: `"url": "${ATLAS_MCP_URL:-http://localhost:8090/mcp}"`, `"Authorization": "Bearer ${ATLAS_MCP_BEARER}"`.
- **Values** come from the environment Claude Code starts in: shell, or the `env` key of `.claude/settings.local.json` (applied once the workspace is trusted). For short-lived tokens use `headersHelper`; a repo-supplied helper gets no `*TOKEN*`/`*SECRET*`/`*KEY*` variables and must read a file or credential store.
- **Every repo whose `.mcp.json` points at a host service sets that URL in its own kit environment** (`ATLAS_MCP_URL: "http://host.docker.internal:8090/mcp"`). Without it the placeholder default `localhost` is the sandbox itself (`ECONNREFUSED`). A second repo using the same server needs the same entry.
- **In `sbx`, the intended route is the MCP gateway:** `sbx mcp add` on the host, OAuth and secrets stay on the host, `--static-mcp` fixes the set at creation. Use `.mcp.json` placeholders for servers that are not in the gateway.
- **Remote MCP with OAuth** (MCP authorization spec 2026-07-28: OAuth 2.1 for HTTP, client ID metadata documents preferred) needs a browser. In a headless sandbox, sign in with `claude mcp login <name> --no-browser`, use a pre-registered client, or fall back to a bearer token through the proxy.
- **stdio servers via `uvx`/`npx`** download on first start. Pin versions (`pkg@1.2.3`, `git+https://...@<tag>`) rather than `@latest`, and pre-install them in the kit's install step so the first session neither waits nor hits the policy.
- **Serena rewrites `.serena/project.yml`** from the template of the installed version (new keys, refreshed comments) whenever that version changes. Pin the same version for host and sandbox (one `.mcp.json` does that) and commit the refreshed file once; two versions rewrite it back and forth.
- **Move repo-local MCP state out of the repo** when a server runs on both sides: Playwright MCP with `--output-dir` (or `PLAYWRIGHT_MCP_OUTPUT_DIR`) and `--isolated`; Serena with `project_serena_folder_location` in `serena_config.yml`.
- **Claude Code's own config in containers:** `~/.claude.json` lives outside `~/.claude`. In a dev container, mount a named volume at the user's `.claude` and point `CLAUDE_CONFIG_DIR` at it; never bind-mount the host's `~/.claude`, `~/.ssh` or cloud credentials.

## Kit for `sbx`

Keep the repo's kit in the repo (e.g. `.sbx/<name>/spec.yaml`, any directory works) and review it like code. Use **schema v2** for a mixin on top of a built-in agent (`sbx run claude --kit ./.sbx/atlas`): the built-in agents select v2 kits, and v3 kits cannot be combined with v1 or v2. v3 (`<name>.yaml` plus a Dockerfile, sbx 0.45+) is for custom workloads. v1 (`commands:`, `network.allowedDomains`) still loads with deprecation warnings; migrate it.

```yaml
schemaVersion: "2"
kind: mixin
name: atlas-dev
environment:
  variables:
    ATLAS_API_URL: "http://host.docker.internal:8000"
setup:
  install:
    - description: Install Task
      command: "npm install -g @go-task/cli"
      user: "0"
    - description: Install uv and pre-warm pinned MCP servers
      user: "1000"
      command: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ~/.local/bin/uv tool install "git+https://github.com/acme/code-index@v1.4.0"
permissions:
  network:
    allow:
      - astral.sh
      - pypi.org
      - files.pythonhosted.org
      - registry.npmjs.org
      - github.com
      - codeload.github.com
      - objects.githubusercontent.com
      - git.example.com
```

- Install as the agent user (`"1000"`); root (`"0"`, the default) only for system paths.
- Pre-warm everything large or slow (tool environments, model downloads) at install, not at first use.
- `sbx kit validate ./.sbx/atlas` before committing; local relative paths must start with `./`. A kit can also come from a Git URL pinned to a commit (`git+https://...#ref=<sha>&dir=<dir>`).
- **A sandbox reads its kit only when it is created.** After changing the kit, recreate it: `sbx rm -f <name>`, then `sbx run claude --kit ./<kit>` (`sbx kit add` also recreates, and only applies environment, install and allow entries). A running or stopped sandbox keeps its old environment.
- `sbx rm` asks for confirmation; scripts use `sbx rm -f`, or they hang at a prompt that may be hidden.
- The first `sbx run` with a new kit runs the install steps behind a spinner without progress output; large pre-downloads take minutes.
- **Check a sandbox from the host:** `sbx exec <name> printenv <VAR>` shows what the kit set; `sbx exec <name> curl -s -o /dev/null -w '%{http_code}' http://host.docker.internal:<port>/` tests a host service (an MCP endpoint answering 406 to a plain request is reachable). `sbx exec` starts a stopped sandbox; `sbx stop <name>` afterwards.
- For a team, `sbxenv.yaml` (no leading dot) in the repo declares sandboxes and their kits; `~/.sbxenv.yaml` holds personal defaults.

## Audit a repo's sandbox setup

Run these checks against a repo and report each as `item · finding → fix`, most severe first. Apply repo changes only after the owner agrees, keeping each file's line endings (a CRLF file rewritten as LF turns a small change into a whole-file diff); hand host commands (upgrades, `sbx policy`, `chown`, recreating sandboxes) to the human. Verify the result inside a recreated sandbox with `sbx exec` (Kit section) and `/mcp`.

1. **No host Docker socket** mounted into any sandbox, dev container or compose service that runs agent code (`grep -rn docker.sock`).
2. **sbx version** at or above the one this reference was checked against (`sbx version`).
3. **Kit:** schema v2 for a mixin on a built-in agent; no v1 fields (`commands:`, `network.allowedDomains`); `sbx kit validate ./<kit>` passes; the kit is actually tracked (`git ls-files .sbx`; the common Vim swap rule `[._]s[a-v][a-z]` in `.gitignore` matches `.sbx` and needs `!/.sbx/`); install steps that write outside system paths run as `user: "1000"`; large downloads pre-warmed.
4. **Network:** host services allowed as `localhost:<port>` (not `host.docker.internal:<port>`); wildcards paired with their bare domain; broad entries justified; rules added on the command line (`sbx policy ls`) copied into the kit.
5. **Compose:** every service that writes into the bind mount has `user: "${UID}:${GID}"` and a writable `HOME`; `node_modules`, the venv and package stores are out of the mount; ports bind to `127.0.0.1`.
6. **IDs exported:** the Taskfile (or an untracked `.env`) sets `UID` and `GID`; no reliance on `${UID:-1000}`.
7. **Ownership now:** `find . -xdev ! -user "$(id -u)" -not -path '*/node_modules/*'`, worktrees included; list the paths and the repair command.
8. **MCP:** committed `.mcp.json` has placeholders only, no literal tokens or internal hosts that belong in env; `uvx`/`npx`/`git+` servers pinned; servers that write repo-local state run on one side or have it moved out; URLs to host services configurable (`${VAR:-http://localhost:<port>}`) and set in this repo's kit environment; app state and the venv pointed outside the workspace.
9. **Secrets:** none in the kit, `.mcp.json` or committed settings; sandbox values through `sbx secret` or the MCP gateway.
10. **Stack inside the sandbox** (if the agent should run integration tests itself): a compose overlay passes the sandbox proxy and CA to the containers; external APIs the stack calls are in the kit; services that need migrations wait for a healthy backend.
11. **CLAUDE.md:** says which sandbox kind the repo uses, which commands run in the sandbox, which the human runs on the host, and the URLs of host services.

## Troubleshooting

| Symptom | Cause | Fix |
|-|-|-|
| `sbx run`/`create`: `500 ... failed to run sandbox container`; daemon log `unknown volume driver: block` | Before sbx 0.47 on Linux: sandboxd started without `/usr/sbin` on PATH, did not find `mkfs.ext4` and disabled its block volume driver; `sbx diagnose` stays green | Upgrade (0.47 bundles `mkfs.ext4`), or add `/usr/sbin:/sbin` to PATH and restart the daemon. Log: `~/.local/state/sandboxes/sandboxes/sandboxd/daemon.log` |
| Tests or MCP calls fail with connection errors only in the sandbox | Domain or host port not allowed (`sbx policy log` shows `deny`) | Allow it; host ports as `localhost:<port>` |
| `curl` to a host service from inside answers HTTP 500 with `dial tcp … connection refused` | The sandbox proxy answers itself: nothing listens on the host port | Start the service on the host |
| `curl` answers HTTP 403 `Approval required for <host>` | No allow rule; the request waits as a pending approval | `sbx policy approval ls`, then `sbx policy approval respond <id> --option allow`, or add the host to the kit |
| `sbx policy log` shows `forward … dial failed` for a host port | The rule allows it, but nothing listens on the host (service not started, wrong port) | Start the service on the host; check with `ss -ltn` |
| MCP server fails with `ECONNREFUSED at ${VAR}` | `VAR` is not set in the sandbox, so the `localhost` default is the sandbox itself | Set the host URL in this repo's kit environment and recreate the sandbox |
| Kit change has no effect | The sandbox was created before the change | `sbx rm -f <name>`, then `sbx run … --kit …` |
| Script hangs after `sbx rm` | Confirmation prompt (possibly hidden by output redirection) | `sbx rm -f` |
| First `sbx run` shows only a spinner for minutes | Kit install steps and pre-downloads run without progress output | Wait; if it never finishes, `sbx policy log` for a blocked download domain |
| `sbx login`: `token is expired` | Device code confirmed too late, or a stale session | `sbx login` again and confirm promptly; otherwise `sbx logout` first |
| pnpm refuses to start or link after the store moved | Old `node_modules` volume, or a pnpm call without the store setting | `up -V`; `ENV npm_config_store_dir` in the image (File ownership) |
| Kit warns `allowedDomains` deprecated, or v2 rejects `commands:` | v1 kit fields | Migrate to v2 (`setup.install`, `permissions.network.allow`) |
| `sbx run claude --kit ./x` fails on a v3 kit | v3 cannot mix with the v2 built-in agents | Use a v2 mixin |
| Kit works locally but is missing for colleagues or in git | `.gitignore` swap-file rule `[._]s[a-v][a-z]` matches `.sbx` | Add `!/.sbx/` after it; check with `git check-ignore -v .sbx/<name>/spec.yaml` |
| Host cannot delete files in the repo | A container or install step wrote as root | File ownership above |
| Files show UID 1000 on a host whose user is not 1000 | `${UID:-1000}` fell back because `UID`/`GID` were not exported | Export from the Taskfile or `.env` |
| Dependencies behave differently on host and in sandbox | Shared `.venv` or `node_modules` built on the other side | Separate environments per side |
| A container inside the sandbox fails with `No address associated with hostname` or cannot reach an external API | Containers do not inherit the sandbox's proxy or CA | Compose overlay with the proxy, `NO_PROXY` and CA bundle (Stack inside the sandbox) |
| `no space left on device` while building images in the sandbox | Docker disk default 10 GB | Recreate with `DOCKER_SANDBOXES_DOCKER_SIZE=40g` (`/sandbox --stack`) |
| `sbx daemon start` stays in the foreground ("not daemonized") | Foreground is the default | `sbx daemon start -d` |
| `sbx ls` or `run`: not authenticated | Docker login expired | `sbx login` |
