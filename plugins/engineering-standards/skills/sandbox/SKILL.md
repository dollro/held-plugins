---
name: sandbox
description: "Starts Claude Code in a Docker Sandbox (sbx) for a repo: creates a git worktree on a new branch (or uses the current checkout, or a private clone), creates the sandbox with the repo's kit, the right mounts and git push over SSH (GitHub, GitLab, self-hosted), checks it from outside (git, kit environment, host services) and hands over one line to attach. Gives the sandbox the user's own Claude Code harness (marketplaces, plugins, skills, CLAUDE.md, settings, MCP servers) from a personal kit the user reviews item by item. Also tears it down after the merge. Use when someone says /sandbox <type>/<name>, /sandbox, /sandbox --clone, /sandbox --done <name>, /sandbox harness, \"same plugins in the sandbox\", \"run Claude in a sandbox\", \"sandbox for this branch/worktree\", \"start a sandboxed agent\", \"git push fails in the sandbox\", \"Sandbox starten\". Background and troubleshooting: engineering-standards references/agent-sandbox.md."
---

# Sandbox

Set up a Docker Sandbox (`sbx`) so the user can run Claude Code inside it on a branch of this repo. Claude prepares and checks everything; the user only types the final `sbx run --name …` line in a terminal, because that opens an interactive session Claude cannot drive.

The script is `<this skill>/scripts/sandbox.sh`. Its lines start with `OK`, `WARN`, `FAIL`, `INFO` or `ATTACH`. Never run `sbx run` or `sbx login` yourself; both are interactive.

Argument `$ARGUMENTS`, one of:

- `<type>/<short-name>`: new worktree on a new branch, plus its sandbox (the usual case)
- empty: a sandbox for the current checkout or worktree
- `--clone`: a sandbox on a private clone of the repo, nothing on the host checkout changes
- `--done <sandbox-name>`: tear down after the work is merged
- `harness`: build or refresh the personal harness kit (Harness below)
- `--stack` added to any of the above: the agent will run the Docker stack and its integration tests inside the sandbox (its own Docker engine). The sandbox gets a 40 GB Docker disk and 12 GB memory (`--docker-size`, `--memory` to change); sizes are fixed at creation
- `--recreate` added to any of the above: rebuild an existing sandbox (needed after a kit change)
- `--no-git-auth` added to any of the above: skip the git push setup below; `git push` then runs on the host
- `--host-key '<alg> <base64>'`: the git server's SSH host key, verified out of band (first two fields of its `/etc/ssh/ssh_host_ed25519_key.pub`)
- `--no-harness` added to create: a bare Claude Code without the user's harness kit

## Set up

1. **Preflight.** `bash <this skill>/scripts/sandbox.sh preflight`. On `FAIL`, stop and give the user the one fix from the output: install sbx, `sbx daemon start -d`, or `sbx login` in their own terminal (device code in the browser, confirm promptly). Continue when preflight passes. Its harness line: `INFO no Claude Code harness kit` or `WARN … stale` / `new since the last selection`: offer to run the Harness flow below first (one question); the sandbox works without it, just with a bare Claude Code.
2. **Branch name** (only for `<type>/<short-name>`): the same rules as `/branch`: `<type>` is a commit type of the engineering-standards profile, `<short-name>` lowercase kebab-case; propose a correction and ask once if needed. Base branch: the one the repo's CLAUDE.md names; otherwise the script uses `develop` if it exists, else the remote default. Pass `--base <branch>` when the CLAUDE.md names one.
3. **Create.**
   - New branch: `bash <this skill>/scripts/sandbox.sh create --branch <type>/<short-name> [--base <branch>]`. The worktree goes next to the main checkout as `../<repo>-<short-name>`.
   - Current checkout: `bash <this skill>/scripts/sandbox.sh create` (from inside it), or `--path <dir>`.
   - Clone: `bash <this skill>/scripts/sandbox.sh create --clone`.

   Add `--stack` when the user asked for it or wants the agent to run integration tests itself; suggest it when the repo's CLAUDE.md says the agent runs the stack inside the sandbox.

   The first creation runs the kit's install steps and can take minutes; say so before starting. For a linked worktree the script mounts the main repo's `.git` as a second, writable workspace automatically.

   **Git push from the sandbox.** Before creating anything, the script reads the push URL of `origin` and prepares what `git push`/`pull` inside needs (background: engineering-standards `references/agent-sandbox.md`, Git hosts):
   - SSH remote (`git@host:…`, `ssh://…`): adds Docker's contributed kit that pins the host key in the sandbox (`github-ssh` for github.com, `gitlab-ssh` with `host` and `hostKey` for any other host, self-hosted GitLab included). The key itself never enters the sandbox: sbx forwards the host's ssh-agent when the user attaches.
   - HTTPS remote to github.com: checks the `github` service secret; the proxy injects it.
   - HTTPS remote to any other host: warns that it cannot authenticate from the sandbox and prints the `git remote set-url … git@host:…` line. Offer it; it changes the shared `.git/config`, and the host keeps working over SSH.
4. **Git prerequisite missing** (exit code 4): nothing was created. Give the user the one fix from the `FAIL` line, for their own terminal, then run step 3 again:
   - `kit source github.com/docker/ not allowed`: the printed `sbx settings set kit.allowedSources '[…]'` (keeps the existing entries, adds `github.com/docker/`).
   - `could not get the SSH host key`, or `differs from what the server answers now`: ask for the key from the server's admin, pass it with `--host-key`. A mismatch can mean a man-in-the-middle; never just take the new key.
   - Or `--no-git-auth` when the user prefers to push from the host.
5. **No kit** (exit code 3, `FAIL no sandbox kit`): the repo has no `.sbx/<name>/spec.yaml`. Offer to write one from the template in engineering-standards `references/agent-sandbox.md` (Kit section, then its audit), commit it on the repo's base branch with the owner's agreement, and run step 3 again. Do not invent network rules: derive them from the repo's MCP servers, package managers and the services its tests call.
6. **Read the check** the script prints after creating (or run `sandbox.sh check <name>` for an existing sandbox):
   - `git in sandbox: ## <branch>` must be `OK`.
   - `WARN env … kit says …`: the sandbox is older than the kit; rerun with `--recreate`.
   - `WARN host service … nothing listening`: a service the kit points at is not running on the host. Name the host command that starts it (from the repo's CLAUDE.md), for the user to run; the sandbox itself is fine.
   - `WARN host service … blocked by policy`: the port is missing from the kit's allow list.
   - `WARN sandbox … already exists`: kit and mounts are fixed at creation; offer `--recreate` if the kit or mounts changed, otherwise just attach.
   - A new worktree has no ignored files (`.env`, decrypted secrets, local settings). If the repo needs them, name which ones, and copy them from the main checkout once the user agrees; they are then readable inside the sandbox.
   - `WARN host key … from ssh-keyscan (trust on first use)`: show the fingerprint and ask the user to compare it with the server's (`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` on the server, or the fingerprint the git host publishes). On a mismatch: `sandbox.sh done <name> --force` and create again with `--host-key`. `OK host key … from your known_hosts` means the user's machine already trusts it.
   - `WARN ssh-agent holds no key` / `no ssh-agent reachable`: before attaching, `ssh-add ~/.ssh/<key>` in the terminal the user attaches from (`ssh-add -l` lists it). The agent is forwarded at attach time; without a key, push inside fails with `Permission denied (publickey)`.
   - `WARN git: no SSH host key for <host> in the sandbox` (a sandbox created before this, or with `--no-git-auth`): the printed `sbx kit add <name> …` line adds the kit without losing work. It recreates the container: a running session ends, kit volumes and session state stay, resume with `claude --continue`. Sandboxes too old for `sbx kit add` are refused; then `--recreate`. Needs the kit source allowed (step 4).
   - `WARN git over HTTPS to github.com needs the github secret`: the user runs `sbx secret set github --command 'gh auth token'` (or `sbx secret set github` and pastes a token).
   - `WARN harness: not in sandbox` / `older than the kit`: the printed `sbx kit add <name> <kit>` brings it in without losing work (recreates the container, like the git kit). `WARN harness install: …`: a marketplace or plugin failed inside; see Harness, troubleshooting.
   - With `--stack`: `WARN no compose overlay` means containers inside will not reach external services. Offer to add the overlay from engineering-standards `references/agent-sandbox.md` (Stack inside the sandbox) and the external hosts to the kit, committed on the base branch with the owner's agreement.
7. **Hand over** in a short block:
   - The attach line from `ATTACH:` alone in a code block, for a terminal (not with `!`, it is interactive). The first start inside may ask for `/login`.
   - Where it runs: branch and folder; commits made inside land on that branch on the host at once.
   - The split, briefly. Without `--stack`: inside the sandbox the agent edits, lints, type-checks and runs unit tests; the Docker stack, migrations and end-to-end tests run on the host, and a stack started from a worktree uses the same compose project and database as the main checkout unless started with its own `-p` and ports. With `--stack`: the agent builds, starts and tests the stack inside the sandbox with the overlay (the commands from the repo's CLAUDE.md); the first build takes minutes, later test rounds are fast, and the host stack is untouched.
   - Git: with the git setup `OK`, the agent pushes and pulls inside with plain `git`; first test inside: `ssh -T git@<host>` (SSH) or `git ls-remote origin`. Otherwise `git push` runs on the host.
   - Back later: the same `sbx run --name …` line. Done: `/sandbox --done <name>`.

## Harness (`harness`)

The sandbox's Claude Code starts bare: no plugins, no user CLAUDE.md, default settings. `sandbox.sh harness` builds a personal kit (v2 mixin) from the user's host setup at `${XDG_CONFIG_HOME:-~/.config}/sbx-kits/claude-harness/`, outside any repo (never commit it). `create` then adds it automatically, with `--skills off` (the kit carries the chosen skills) and `--static-mcp <chosen servers>`. Background: engineering-standards `references/agent-sandbox.md`, Claude Code harness in the sandbox.

1. `bash <this skill>/scripts/sandbox.sh harness`. The first run (and any run that finds new candidates) writes `harness.selection.json` next to the kit, prints it as `TABLE` lines (`[on ]`/`[off]`, `NEW`, a reason for default-off items) and exits 5 without building anything.
2. **Ask the user what to leave out.** Show the table compactly, grouped by category (marketplaces, plugins, skills, MCP servers, files, settings). Ask with AskUserQuestion, `multiSelect: true`, one question per category, at most 4 options each: the items most worth deciding on (default-off items with their reason, plugins and MCP servers that touch the host or other systems); mention that the user can name any other item in "Other". Only `NEW` items need a decision on later runs; earlier decisions are kept.
3. Edit `harness.selection.json`: set `"enabled": false` (or `true`) per the answers. Never add secrets; `networkAllow` takes extra host names only (see troubleshooting).
4. `bash <this skill>/scripts/sandbox.sh harness --yes` builds the kit: `OK … N plugin(s) …`, `INFO … left out: …`. Relay:
   - `WARN private GitHub marketplaces … github secret`: the user runs `sbx secret set github --command 'gh auth token'`.
   - `WARN MCP server <name> is selected but not registered with sbx`: MCP configs are not copied (they hold tokens). The user registers it on the host with `sbx mcp add` (credentials stay on the host), then reruns step 4; registered servers reach the sandbox through the sbx MCP gateway via `--static-mcp`. MCP servers of a plugin come and go with the plugin.
   - `FAIL local kits are disabled`: the printed `sbx settings set kit.allowLocalKits true`, for the user's terminal.
5. New sandboxes get it on create. Existing ones: `sbx kit add <name> <kit-dir>` (recreates the container, keeps state). `check` reports a stale kit, new candidates and a sandbox older than the kit.

What it carries: marketplaces (`claude plugin marketplace add`) and enabled plugins (`claude plugin install --scope user`) as the agent user at creation; `~/.claude/CLAUDE.md`, user agents, commands and output styles; the status line script; selected skills; an allowlist of settings keys merged into the agent's existing `settings.json`. Never: credentials, `~/.claude.json`, history, projects or memory, `env`, `permissions`, `hooks`, MCP configs. Files that look like they hold a secret are refused.

Troubleshooting: `WARN harness install: marketplace … SSH host key is not in your known_hosts`: Claude Code fell back from HTTPS to SSH after the HTTPS clone failed, usually git submodules on a host the kit does not allow, or a very large clone. `sbx policy log <name>` names the host; add it to `networkAllow` in the selection, or leave the marketplace off (marketplaces without an enabled plugin are off by default). A plugin whose install runs a marketplace-declared command is not confirmed automatically (no `-y`); it shows up as failed and is installed by hand inside.

## Tear down (`--done <name>`)

`bash <this skill>/scripts/sandbox.sh done <name>`. For a worktree it refuses while there are uncommitted changes or unpushed commits; for a clone it refuses until the agent's work is fetched (`git fetch sandbox-<name>`, then branch or merge it). Show the refusal and its fix; use `--force` only when the user confirms the work may be discarded. It removes the sandbox, the worktree and the branch if merged, and never the main checkout.

## Rules

- One sandbox per worktree. Two agents in one worktree overwrite each other's files.
- Never mount the host Docker socket; never put secrets into the kit or the command line.
- The harness kit is personal: it stays outside every repo, and it is rebuilt from the user's host config, never edited by hand except `harness.selection.json`.
- Never mount `~/.ssh` or copy a private key into a sandbox; SSH goes through the forwarded agent. For git over HTTPS to a host other than github.com, no custom secret, `insteadOf`, `http.extraHeader` or credential helper: they cannot work through the proxy or put the token inside.
- Language: mirror the user's; commands and branch names in English.
