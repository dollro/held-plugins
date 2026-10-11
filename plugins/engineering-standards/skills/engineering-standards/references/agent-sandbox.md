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

For letting the agent run unattended in a sandbox (who decides where it runs, `/goal`, Stop hooks, headless runs, review before merge), see `autonomous-runs.md`. `sbx run claude` starts Claude with permissions skipped by default, so the sandbox boundary is the safety net.

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
    ELECTRON_GET_USE_PROXY: "1"   # only if a container downloads Electron
  x-sbx-ca: &sbx-ca
    - /etc/ssl/certs/ca-certificates.crt:/sbx-ca/ca-certificates.crt:ro   # system CAs + proxy CA
  services:
    django:  { environment: *sbx-proxy, volumes: *sbx-ca }
    realtime: { environment: *sbx-proxy, volumes: *sbx-ca }
    worker:  { environment: *sbx-proxy, volumes: *sbx-ca }
  ```

  The proxy address and bundle path are what the sandbox itself uses (`env | grep -i proxy` inside it). Check them when sbx changes. Image builds (`docker build`, `buildx bake`) already go through the proxy; only running containers need the overlay.
- **One Taskfile for host and sandbox.** Detect the sandbox with `$SANDBOX_NAME` (set by sbx) and let only the compose files or `docker run` flags differ (`-f compose.sbx.yml` inside). Tasks that need host-only things (a display, SSH or SOPS keys, host-installed tools) stop early with a message naming the alternative, instead of failing halfway:

  ```yaml
  # Taskfile.yml
  vars:
    COMPOSE: 'docker compose -f compose.local.yml{{if .SANDBOX_NAME}} -f compose.sbx.yml{{end}}'
  tasks:
    secrets:decrypt:
      preconditions:
        - sh: test -z "$SANDBOX_NAME"
          msg: "No SOPS key in the sandbox: run 'task secrets:decrypt' on the host, then copy the env file in."
  ```
- **No apt mirrors on the allow list.** `apt-get install` inside a container fails; prefer images that already carry the dependencies (the Playwright image has xvfb and the libraries Electron needs) over installing at run time.
- **External APIs the stack calls go into the kit's allow list** (speech-to-text, LLM providers); otherwise they fail with HTTP 403 `Approval required`.
- **Gitignored files a new worktree lacks** (decrypted env files) must be copied in before `up`; they then sit inside the sandbox where the agent can read them. Decrypt on the host and copy the file in once; the sandbox never holds the SOPS key.
- **What may enter the sandbox:** local-only secrets (dev database passwords, local signing keys) are fine. Production files and keys never. Paid third-party APIs get separate dev keys with spending caps, because the agent can read and use them.
- **Ports stay inside the sandbox.** Parallel sandboxes each run their own stack on the same ports without colliding; publish one to the host only to look at it (`sbx ports <name> --publish <host>:<port>`; services listen on `0.0.0.0`).
- **Ownership is fine.** A container running as root inside the sandbox writes files that appear on the host owned by the host user (tested on a host with UID 1000, the same as the agent user's; rerun `touch` from a container and `ls -ln` on the host when the UIDs differ).
- **Integration tests are usually deselected by default** (a marker such as `-m 'not integration'` in the pytest config) because they need live API keys and outside services. Inside the sandbox they run when the keys are in the copied env file and every host they call is in the kit; run them explicitly (`pytest -m integration`). A `403 Approval required for <host>` in the output names the next host for the kit's allow list.
- **Report the whole count, not just "passed".** A green run with deselected or skipped tests did not exercise those paths; the agent states passed, failed, skipped and deselected (and why) before calling the work verified.
- **Warnings from the app show up as well.** A teardown warning such as `database "test_…" is being accessed by other users` comes from the code (a test or client leaving a connection open), not from the sandbox; a fresh stack in a sandbox is a good place to fix it, because the agent can rerun the suite itself.
- **Startup order shows up here first.** A clean stack in a fresh sandbox exposes races a long-lived host stack hides, such as a scheduler starting before migrations; use `depends_on: … condition: service_healthy`.

#### Test loop: how the agent runs the suite

1. **Copy the CI job.** Read the job that runs the suite (`.gitlab-ci.yml`, the GitHub workflow) and reuse its compose files, images and command order. Do not invent a separate flow.
2. **Tools run in containers, not in the sandbox.** Missing pnpm or browsers are not installed into the sandbox; use the image CI uses, pinned to the project's version (for E2E the official Playwright image matching `@playwright/test` in `package.json`).
3. **Throwaway overlays stay out of the repo.** One-off compose files (a tool container, a production-like setting) go into the agent's scratchpad and are added with another `-f`. Relative paths in them resolve against the first compose file's directory. An `environment:` entry in an overlay overrides the service's `env_file` (e.g. switch the app from the Vite dev server to built assets). If the overlay is worth keeping, commit it next to `compose.sbx.yml`.
4. **Tool containers follow the same rules:** the proxy/CA block above (with every compose service name in `NO_PROXY`) and `user: "${UID}:${GID}"` with `HOME` under `/tmp` (File ownership below). For pnpm as non-root, set `COREPACK_HOME` to a writable path and `corepack enable --install-directory <writable dir>`. Escape `$` as `$$` inside a compose `command:`.
5. **Start only what the tests need:** `up -d --wait <services>`, not the whole stack.
6. **Long runs:** send build and test output to a log file in the scratchpad and read it with `tail`; wrap commands in `timeout`; raise the Bash tool timeout (up to 600000 ms) instead of polling.
7. **`exec` into running services.** `docker compose run --no-deps <svc>` hangs when the entrypoint waits for a database that is not part of the run.
8. **Check the result, not just exit code 0:** print the versions and settings that matter from inside the container (`exec`), search the logs for warnings and tracebacks, check `docker inspect -f '{{.RestartCount}}' <container>` for crash loops, confirm `git status` is clean, and state what the run did not cover (local images instead of CI's, production-only settings).
9. **Habits that saved time:**
   - Cleanup steps (`defer` in Task) delete the logs and containers you need to debug; reproduce a failure by running the steps by hand.
   - Python `read_text`/`write_text` turns CRLF into LF; a whole-file change in `git diff --stat` is the giveaway. Preserve line endings when editing files programmatically.
   - Local images are not rebuilt when you switch branches; rebuild (`up --build`) before trusting a run on another branch.

Stack lessons that hold without a sandbox (atomic secret decryption, isolating a second compose project, migrations on a fresh database, pinned tool versions, local bake overrides) live in `fullstack-engineering` (`local-dev-and-tooling.md`, `secrets-and-config.md`, `ci-cd-and-deploy.md`).

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

## Git hosts: push and pull from the sandbox (`sbx`)

The agent should commit, push and pull inside the sandbox with plain `git` against the repo's existing remote. No private key enters the sandbox: SSH goes through the host's ssh-agent, which sbx forwards when you attach (`ssh.agentForwardingEnabled`, on by default), and HTTPS tokens stay at the proxy. What blocks out of the box is SSH host-key verification (no TTY to accept a new key, so `Host key verification failed`) and, for HTTPS, the auth scheme. `/sandbox` sets this up from the `origin` push URL; this is what it does and why.

| Remote | Route | Setup |
|-|-|-|
| GitHub, HTTPS | Built-in `github` service secret; the proxy injects it for `github.com` (git push over HTTPS not tested here) | `sbx secret set github --command 'gh auth token'` (or `sbx secret set github`, paste a token) |
| GitHub, SSH | Forwarded ssh-agent plus GitHub's host keys | Kit `github-ssh` (fetches the keys GitHub publishes at `api.github.com/meta`) |
| GitLab or another self-hosted host, SSH | Forwarded ssh-agent plus the pinned host key | Kit `gitlab-ssh` with `host` and `hostKey` (gitlab.com's keys are built in) |
| GitLab or another self-hosted host, HTTPS | Does not work through the proxy | Switch the remote to SSH: `git remote set-url origin git@git.example.com:acme/atlas.git`, then the row above |

**Why HTTPS fails for GitLab.** GitLab's git-over-HTTP accepts Basic auth (the token as password, any username such as `oauth2`) or Kerberos, not a Bearer or `PRIVATE-TOKEN` header. The sbx proxy only swaps a literal placeholder it finds in a header (`sbx secret set-custom`), and inside a base64 Basic header there is no literal placeholder to find. Docker's `gitlab` kit hit the same wall: two inject rules on one host are not told apart by scheme, and GitLab serves the API and git from one host. sbx handles git Basic auth only for its built-in `github` service. The `gitlab` kit (glab with a token) is useful for the API, never for git.

Kits come from Docker's contributed collection, `git+https://github.com/docker/sbx-kits-contrib.git#dir=<kit>` (pin with `#ref=<sha>&dir=<kit>` for a team).

1. **Allow the kit source once.** `sbx settings get kit.allowedSources` defaults to `["docker.io/"]`; a git kit from Docker's GitHub is refused until its prefix is listed. Keep the existing entries and add it: `sbx settings set kit.allowedSources '["docker.io/","github.com/docker/"]'`. (The kits are also published as `docker.io/sbx/<kit>-kit:latest`, which the default admits; unpinned.)
2. **Load the key on the host.** `ssh-add -l` must list the key registered with the git host, in the terminal you attach from. The socket is forwarded even when the agent is empty; then push fails inside with `Permission denied (publickey)`.
3. **Get the host key and verify it out of band.** `ssh-keyscan -t ed25519 git.example.com 2>/dev/null | grep -v '^#' | cut -d' ' -f2,3` gives `ssh-ed25519 AAAA…`, but scanning is trust on first use. Compare its fingerprint (`ssh-keygen -lf -` on the scan output) with the server's (`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`, from the admin), or take the key from your own `~/.ssh/known_hosts` if you verified it before (`ssh-keygen -F git.example.com`).
4. **Attach the kit.**

   ```bash
   # new sandbox
   sbx create claude --kit ./.sbx/atlas \
     --kit "git+https://github.com/docker/sbx-kits-contrib.git#dir=gitlab-ssh" \
     --kit-arg host=git.example.com --kit-arg "hostKey=ssh-ed25519 AAAA…" ~/src/atlas
   # existing sandbox, keeps its work
   sbx kit add claude-atlas "git+https://github.com/docker/sbx-kits-contrib.git#dir=gitlab-ssh" \
     --kit-arg host=git.example.com \
     --kit-arg "hostKey=$(ssh-keyscan -t ed25519 git.example.com 2>/dev/null | grep -v '^#' | cut -d' ' -f2,3)"
   ```

   `sbx kit add` recreates the container: a running session ends, kit volumes and session state stay (resume with `claude --continue`). Sandboxes created before sbx could recreate are refused; recreate those (`sbx rm -f`, then create). The existing `git@` remote and the shared `.git/config` stay as they are.
5. **Test inside.** `ssh -T git@git.example.com` greets you by user name; then `git fetch` and `git push`.

The `gitlab-ssh` kit only pins a host key, so it serves any SSH git host on port 22 (Gitea, Bitbucket Server); GitHub has its own. Not covered: SSH on another port (the pinned entry is for port 22) and host aliases from `~/.ssh/config`, which the sandbox lacks; use the real host name in the remote, or push from the host.

**Don't:**

- mount `~/.ssh` or copy a private key into the sandbox; the agent could read and send it;
- wire GitLab git over HTTPS with `sbx secret set-custom`, `url.<base>.insteadOf`, `http.extraHeader` or a credential helper: the placeholder is never substituted, or the real token sits inside the sandbox;
- accept a host key that differs from the one you trusted before without asking the server's admin.

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

## Claude Code harness in the sandbox (`sbx`)

The built-in `claude` agent starts bare: no plugins or marketplaces, no user `CLAUDE.md`, default settings. The user's harness belongs in a **personal** kit, not in the repo's kit: it differs per person and holds their instructions. `/sandbox harness` (`sandbox.sh harness`) builds it from the host's user-level setup at `${XDG_CONFIG_HOME:-~/.config}/sbx-kits/claude-harness/` and `/sandbox` adds it to every sandbox it creates.

**Build it before the first sandbox.** Order on a new machine: `/sandbox harness` (personal kit, once, refreshed when the host setup changes), then `/sandbox` on the current branch, or `/sandbox <type>/<name>` for a new worktree branch (the repo's kit plus the harness). A sandbox created without it stays bare until `sbx kit add <name> <kit-dir>`, which recreates the container.

**The user picks what goes in.** `harness.selection.json` next to the kit lists every candidate with `"enabled": true|false`; the first run, and every run that finds something new, stops after printing it (exit 5) until the user has decided and reruns with `--yes`. Decisions are kept; only new items are asked about. Defaults: what is enabled on the host is on, except plugins that drive a browser or the desktop, marketplaces no enabled plugin comes from, MCP servers that are not registered with sbx (host services, credentials), and files that look like they hold a secret.

| Item | Host source | In the sandbox |
|-|-|-|
| Marketplaces | `extraKnownMarketplaces` in `~/.claude/settings.json`, `~/.claude/plugins/known_marketplaces.json` | `claude plugin marketplace add <owner/repo or URL> --scope user` at creation, as the agent user. Directory sources are skipped (host path) |
| Plugins | `enabledPlugins: true` | `claude plugin install <name>@<marketplace> --scope user` (no `-y`: plugins installed by a marketplace-declared command fail visibly instead of being accepted) |
| Skills | `~/.claude/skills/*` and the sbx skills store (`sbx skills ls`) | Copied by the kit; the sandbox is created with `--skills off`, so a skill left out stays out. `sbx skills import` is the shared alternative, but its store is linked into every sandbox and cannot be filtered per sandbox |
| MCP servers | User-scope servers in `~/.claude.json` (names and transport only) and `sbx mcp ls` | Configs are never copied (headers and env hold tokens). Registered servers go in with `--static-mcp`; others are registered on the host first with `sbx mcp add` (MCP section). A plugin's own MCP servers come with the plugin |
| Files | `~/.claude/CLAUDE.md`, `agents/`, `commands/`, `output-styles/`, the status line script | Written to `/home/agent/.claude/`; the status line path is rewritten |
| Settings | An allowlist: `model`, `effortLevel`, `autoCompactEnabled`, `attribution`, `outputStyle`, `statusLine`, … | Merged key by key into the `settings.json` the agent image already has (python3 or jq), never overwritten |

Never copied: credentials, `~/.claude.json`, history, `projects/` and memory, sessions, `env`, `permissions`, `hooks`, helper commands (`apiKeyHelper` and the like). Content goes inline into the install steps (base64), not as kit files: `sbx kit add` refuses kits with static files or `setup.files`, and this way an existing sandbox can take the kit without losing its state.

- **Network:** the kit allows `github.com`, `codeload.github.com`, `api.github.com`, `objects.githubusercontent.com`, `raw.githubusercontent.com`, the hosts of non-GitHub marketplaces and of git submodules found in the host's clone, plus `networkAllow` from the selection (host names only).
- **Private GitHub marketplaces** clone through the proxy with the `github` service secret (`sbx secret set github --command 'gh auth token'`); the command warns when one is private and the secret is missing. Private marketplaces on other hosts cannot authenticate from the sandbox (the same limit as git over HTTPS in Git hosts).
- **Drift:** the kit stores a hash of what it carries (`harness.sha256`) and the sandbox a stamp (`~/.claude/.sbx-harness.sha256`). `sandbox.sh check` reports a stale kit (host config or selection changed), new candidates, a sandbox older than the kit (fix: `sbx kit add <name> <kit-dir>`) and install failures from `~/.claude/.sbx-harness.log` inside.
- **Install failures do not fail creation.** Each step logs `OK`/`FAIL` per item and exits 0, so one unreachable marketplace does not cost the whole sandbox.
- `kit.allowLocalKits` must be `true` (the default) for a kit from a local directory.

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
10. **Git push from the sandbox:** remote type matches a route in Git hosts (SSH remote plus host-key kit, or GitHub HTTPS with the `github` secret); no mounted `~/.ssh`, no token in `.git/config`, no `insteadOf`/`extraHeader` for the git host; the host key was verified out of band.
11. **Stack inside the sandbox** (if the agent should run integration tests itself): a compose overlay passes the sandbox proxy and CA to the containers; external APIs the stack calls are in the kit; services that need migrations wait for a healthy backend.
12. **CLAUDE.md:** says which sandbox kind the repo uses, which commands run in the sandbox, which the human runs on the host, and the URLs of host services.

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
| `git push` inside: `Host key verification failed` | No known_hosts entry for the git host in the sandbox, no TTY to accept one | Host-key kit (Git hosts); existing sandbox: `sbx kit add` |
| `git push` inside: `Permission denied (publickey)` | Host's ssh-agent empty or not running in the terminal that attached | `ssh-add ~/.ssh/<key>`, check `ssh-add -l`, attach again |
| `git push` over HTTPS to GitLab inside: `HTTP Basic: Access denied` or a prompt for a password | The proxy cannot inject Basic auth for GitLab | SSH remote plus `gitlab-ssh` kit (Git hosts) |
| `sbx create`/`kit add` refuses a kit from `github.com/docker/…` | `kit.allowedSources` does not list it | `sbx settings set kit.allowedSources '["docker.io/","github.com/docker/"]'` |
| `docker compose run --no-deps <svc>` never returns | The entrypoint waits for a database that `--no-deps` did not start | `exec` into the running service, or start its dependencies |
| A container exits with 137 after the agent removed it | Killed by the removal (SIGKILL), not a failure | Nothing to fix |
| `sbx kit add` refuses an older sandbox | Created before sbx could recreate sandboxes | Recreate the sandbox |
| Claude Code inside has none of your plugins or your CLAUDE.md | No harness kit, or the sandbox predates it | `/sandbox harness`, then `sbx kit add <name> <kit-dir>` |
| Harness log: marketplace failed with `SSH host key is not in your known_hosts` | Claude Code fell back from HTTPS to SSH after the HTTPS clone failed: submodules on a host the kit does not allow, or a very large clone | `sbx policy log <name>` for the host, add it to `networkAllow` in `harness.selection.json`; or leave that marketplace off |
| Harness log: plugin install failed, marketplace fine | The plugin installs through a marketplace-declared command that needs confirmation, or its download host is not allowed | Install it by hand inside (`claude plugin install …`), or allow the host |
