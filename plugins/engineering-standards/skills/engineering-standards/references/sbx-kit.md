# Kit for `sbx`

The repo's kit: what every sandbox for the repo installs and may reach. Background (sandbox kinds, network policy, git hosts, MCP) in `agent-sandbox.md`.

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
      # Download, then run: `curl … | sh` exits 0 when the download is blocked.
      command: |
        curl -LsSf -o /tmp/uv-install.sh https://astral.sh/uv/install.sh
        sh /tmp/uv-install.sh
        ~/.local/bin/uv tool install "git+https://github.com/acme/code-index@v1.4.0"
    - description: Put uv on every PATH
      user: "0"
      command: |
        test -x /home/agent/.local/bin/uv || { echo "uv missing: install step failed"; exit 1; }
        ln -sf /home/agent/.local/bin/uv /usr/local/bin/uv
        ln -sf /home/agent/.local/bin/uvx /usr/local/bin/uvx
permissions:
  network:
    allow:
      - astral.sh
      - releases.astral.sh   # the uv installer downloads from here
      - pypi.org
      - files.pythonhosted.org
      - registry.npmjs.org
      - github.com
      - codeload.github.com
      - objects.githubusercontent.com
      - git.example.com
```

- Install as the agent user (`"1000"`); root (`"0"`, the default) only for system paths.
- **Put user installs on every PATH.** uv, `uv tool` and pipx install into `/home/agent/.local/bin`, which git hooks and non-login shells do not see (`pre-commit not found` on commit). A later root step links them: `ln -sf /home/agent/.local/bin/{uv,uvx,pre-commit} /usr/local/bin/`.
- **Install what the repo's checks call:** the git-hook runner (`uv tool install pre-commit`), and pnpm pinned to the version in `package.json`'s `packageManager` (`npm install -g pnpm@<ver>`). Corepack without a `packageManager` field picks an unpinned version and may fail to fetch it.
- Pre-warm everything large or slow (tool environments, model downloads) at install, not at first use.
- `sbx kit validate ./.sbx/atlas` before committing; local relative paths must start with `./`. A kit can also come from a Git URL pinned to a commit (`git+https://...#ref=<sha>&dir=<dir>`).
- **A sandbox reads its kit only when it is created.** After changing the kit, recreate it: `sbx rm -f <name>`, then `sbx run claude --kit ./<kit>` (`sbx kit add` also recreates, and only applies environment, install and allow entries). A running or stopped sandbox keeps its old environment.
- `sbx rm` asks for confirmation; scripts use `sbx rm -f`, or they hang at a prompt that may be hidden.
- The first `sbx run` with a new kit runs the install steps behind a spinner without progress output; large pre-downloads take minutes.
- **Check a sandbox from the host:** `sbx exec <name> printenv <VAR>` shows what the kit set; `sbx exec <name> curl -s -o /dev/null -w '%{http_code}' http://host.docker.internal:<port>/` tests a host service (an MCP endpoint answering 406 to a plain request is reachable). `sbx exec` starts a stopped sandbox; `sbx stop <name>` afterwards.
- For a team, `sbxenv.yaml` (no leading dot) in the repo declares sandboxes and their kits; `~/.sbxenv.yaml` holds personal defaults.

- **Never pipe a download into a shell** (`curl … | sh`). When the policy blocks the download, curl fails, `sh` reads nothing and exits 0: the step passes and the tool is missing. Download to a file, then run it, and let a later step that depends on the result test for it (`test -x … || exit 1`).
- **List the kit's tools in `verify.txt`** next to `spec.yaml`, one command per line (`uv --version`). `sandbox.sh check` runs each inside the sandbox and warns on failure, so a failed install step shows up at creation, not in the agent's first session. It also lists requests the policy blocked (`sbx policy log`), the usual cause.

### Minimal kit for a repo without a stack

A repo of docs, skills or scripts (no Docker stack, no host services) needs only its toolchain and its git host:

```yaml
schemaVersion: "2"
kind: mixin
name: <repo>-dev
setup:
  install:
    - description: Install uv
      user: "1000"
      command: |
        curl -LsSf -o /tmp/uv-install.sh https://astral.sh/uv/install.sh
        sh /tmp/uv-install.sh
    - description: Put uv on every PATH
      user: "0"
      command: |
        test -x /home/agent/.local/bin/uv || { echo "uv missing: install step failed"; exit 1; }
        ln -sf /home/agent/.local/bin/uv /usr/local/bin/uv
        ln -sf /home/agent/.local/bin/uvx /usr/local/bin/uvx
permissions:
  network:
    allow:
      - astral.sh
      - releases.astral.sh
      - pypi.org
      - files.pythonhosted.org
      - registry.npmjs.org        # only if the repo has package.json scripts
      - github.com
      - codeload.github.com
      - objects.githubusercontent.com
```

Plus `verify.txt` with `uv --version`. Add hosts only for what the repo's scripts and tests actually call.
