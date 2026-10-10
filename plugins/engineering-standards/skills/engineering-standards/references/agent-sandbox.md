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

**Default: the agent writes and checks code in the sandbox; the Docker stack runs on the host.**

| Where | What runs there |
|-|-|
| Sandbox (agent) | Editing, git, formatting and lint, type checks, unit tests with the toolchain installed in the sandbox (uv, pnpm, Task), MCP servers that only need the repo or the internet |
| Host (human) | `docker compose` up/down, image builds, migrations against the local database, integration and end-to-end tests against the running stack, deploys, anything that needs real credentials |

Why this stays the default:

- **One stack, one database.** The stack you look at in the browser is the one the agent's edits hot-reload into. A stack inside a sandbox is a second set of images, volumes and data that disappears with `sbx rm`.
- **Ownership.** Containers write into a bind-mounted repo as their image user, often root. On the host that is fixable (see File ownership); for containers run by a sandbox's engine writing into the shared workspace, how ownership maps back to the host is not documented. Test it before relying on it (recipe below).
- **Network.** Image builds pull from distribution mirrors and registries; allowing them widens what the agent can reach for the whole session.
- **The native sandbox cannot run Docker at all.** Its escape hatch, `sandbox.excludedCommands`, runs the listed commands without any filesystem or network limit, and the agent can edit the compose file it then runs. If you use it, keep the pattern narrow (`docker compose *`) and the command on an ask rule.

How the two sides work together:

- The workspace is shared, so the host stack's dev servers (Django runserver, uvicorn `--reload`, Vite) pick up the agent's edits immediately.
- The agent reaches host services as in the table above. Make the URL configurable with a localhost default so the same config works on both sides: `${ATLAS_API_URL:-http://localhost:8000}`, set to the sandbox value in the sandbox environment.
- When a check needs the stack (migrations, integration tests, a rebuild), the agent says which host command to run and why, then continues with the result.
- The repo's CLAUDE.md says this in one place: which commands run in the sandbox, which the human runs on the host, and the URLs of host services.

**Option: the stack inside `sbx`.** Docker documents building and running images and Compose inside a sandbox; services must listen on `0.0.0.0` and are published to the host with `sbx ports <name> --publish <port>` (loopback only). It fits a self-contained stack, parallel agents that each need their own stack, and clone mode (below), where nothing the containers write reaches your checkout. On the shared workspace, run the ownership test first:

```bash
# inside the sandbox, in the workspace
touch agent-file
docker run --rm -v "$PWD":/w alpine touch /w/container-file
# on the host
ls -ln agent-file container-file   # both should show your host UID
```

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

Or let `task setup` write `UID=` and `GID=` into an untracked `.env`.

| Source of foreign-owned files | Example | Fix |
|-|-|-|
| Compose service without a user | A Node/Vite service writes `.pnpm-store/`, `.vite/`, `dist/` as root | `user:` as above |
| Dependencies in the mount | `node_modules`, `.venv` and the pnpm store inside the repo | `node_modules` in a named volume; venv outside the mount (anonymous volume on `/app/.venv`, or `UV_PROJECT_ENVIRONMENT=/opt/venv`); pnpm store in a volume |
| Same environment used on both sides | A `.venv` created in the sandbox, then used on the host | Each side builds its own. A venv records absolute interpreter paths and symlinks and does not move between machines (uv's Docker guide says the same) |
| MCP servers on both sides | A code-index or browser MCP writes repo-local state (`.serena/`, `.playwright-mcp/`) from the sandbox and again from the host | Run each such server on one side, or move its state out of the repo (MCP section) |
| Install steps as root | A kit install command writes into `$HOME` or the repo as root (root is the install default in `sbx` kits) | `user: "1000"` for anything that writes outside system paths |
| Worktrees | A worktree inherits the compose setup and its root-owned output | Same fixes; check worktrees when hunting stray files |

Alternatives, where they fit: dev containers fix the UID automatically on Linux (`updateRemoteUserUID`, on by default); rootless Podman maps your UID with `--userns=keep-id`; Docker Desktop for Linux maps IDs through its VirtioFS share. Plain Docker Engine on Linux has no idmapped bind mounts, so the `user:` fix stays. Compose `develop.watch` syncs host to container only, so container writes never reach the host; files the container must produce for the repo (lockfiles, migrations) then need `docker compose cp` or a bind mount.

Find and repair on the host:

```bash
find . -xdev ! -user "$(id -u)" -not -path '*/node_modules/*' -printf '%u %p\n' | head
docker run --rm -v "$PWD":/w alpine chown -R "$(id -u):$(id -g)" /w/<path>   # no sudo needed
```

Repair is the fallback. Fix the compose file or the kit that produced the files, or they come back.

## Shared workspace or clone (`sbx`)

- **Shared workspace** (default): the sandbox works on the host checkout. Use it for the inner loop: agent edits, host stack hot-reloads, human looks at the result.
- **Clone mode** (`sbx run --clone`, chosen at creation): the host repo is mounted read-only and the agent works on a private clone. Fetch its work with `git fetch sandbox-<name>` while the sandbox runs; `sbx rm` removes that remote. No ownership collisions, and the stack can run inside the sandbox without touching your checkout. Use it for parallel agents and for tasks that should not touch the working copy.
- `sbx run --rm` removes the sandbox when the session ends.

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
- **In `sbx`, the intended route is the MCP gateway:** `sbx mcp add` on the host, OAuth and secrets stay on the host, `--static-mcp` fixes the set at creation. Use `.mcp.json` placeholders for servers that are not in the gateway.
- **Remote MCP with OAuth** (MCP authorization spec 2026-07-28: OAuth 2.1 for HTTP, client ID metadata documents preferred) needs a browser. In a headless sandbox, sign in with `claude mcp login <name> --no-browser`, use a pre-registered client, or fall back to a bearer token through the proxy.
- **stdio servers via `uvx`/`npx`** download on first start. Pin versions (`pkg@1.2.3`, `git+https://...@<tag>`) rather than `@latest`, and pre-install them in the kit's install step so the first session neither waits nor hits the policy.
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
- `sbx kit add` on an existing sandbox recreates it and only applies environment, install and allow entries.
- For a team, `sbxenv.yaml` (no leading dot) in the repo declares sandboxes and their kits; `~/.sbxenv.yaml` holds personal defaults.

## Audit a repo's sandbox setup

Run these checks against a repo and report each as `item · finding → fix`, most severe first. Apply repo changes only after the owner agrees; hand host commands (upgrades, `sbx policy`, `chown`) to the human.

1. **No host Docker socket** mounted into any sandbox, dev container or compose service that runs agent code (`grep -rn docker.sock`).
2. **sbx version** at or above the one this reference was checked against (`sbx version`).
3. **Kit:** schema v2 for a mixin on a built-in agent; no v1 fields (`commands:`, `network.allowedDomains`); `sbx kit validate ./<kit>` passes; install steps that write outside system paths run as `user: "1000"`; large downloads pre-warmed.
4. **Network:** host services allowed as `localhost:<port>` (not `host.docker.internal:<port>`); wildcards paired with their bare domain; broad entries justified; rules added on the command line (`sbx policy ls`) copied into the kit.
5. **Compose:** every service that writes into the bind mount has `user: "${UID}:${GID}"` and a writable `HOME`; `node_modules`, the venv and package stores are out of the mount; ports bind to `127.0.0.1`.
6. **IDs exported:** the Taskfile (or an untracked `.env`) sets `UID` and `GID`; no reliance on `${UID:-1000}`.
7. **Ownership now:** `find . -xdev ! -user "$(id -u)" -not -path '*/node_modules/*'`, worktrees included; list the paths and the repair command.
8. **MCP:** committed `.mcp.json` has placeholders only, no literal tokens or internal hosts that belong in env; `uvx`/`npx`/`git+` servers pinned; servers that write repo-local state run on one side or have it moved out; URLs to host services configurable (`${VAR:-http://localhost:<port>}`) and set in the kit environment.
9. **Secrets:** none in the kit, `.mcp.json` or committed settings; sandbox values through `sbx secret` or the MCP gateway.
10. **CLAUDE.md:** says which sandbox kind the repo uses, which commands run in the sandbox, which the human runs on the host, and the URLs of host services.

## Troubleshooting

| Symptom | Cause | Fix |
|-|-|-|
| `sbx run`/`create`: `500 ... failed to run sandbox container`; daemon log `unknown volume driver: block` | Before sbx 0.47 on Linux: sandboxd started without `/usr/sbin` on PATH, did not find `mkfs.ext4` and disabled its block volume driver; `sbx diagnose` stays green | Upgrade (0.47 bundles `mkfs.ext4`), or add `/usr/sbin:/sbin` to PATH and restart the daemon. Log: `~/.local/state/sandboxes/sandboxes/sandboxd/daemon.log` |
| Tests or MCP calls fail with connection errors only in the sandbox | Domain or host port not allowed | `sbx policy log`; host ports as `localhost:<port>` |
| Kit warns `allowedDomains` deprecated, or v2 rejects `commands:` | v1 kit fields | Migrate to v2 (`setup.install`, `permissions.network.allow`) |
| `sbx run claude --kit ./x` fails on a v3 kit | v3 cannot mix with the v2 built-in agents | Use a v2 mixin |
| Host cannot delete files in the repo | A container or install step wrote as root | File ownership above |
| Files show UID 1000 on a host whose user is not 1000 | `${UID:-1000}` fell back because `UID`/`GID` were not exported | Export from the Taskfile or `.env` |
| Dependencies behave differently on host and in sandbox | Shared `.venv` or `node_modules` built on the other side | Separate environments per side |
| `sbx daemon start` stays in the foreground ("not daemonized") | Foreground is the default | `sbx daemon start -d` |
| `sbx ls` or `run`: not authenticated | Docker login expired | `sbx login` |
