---
name: sbx
description: "Moves Claude Code work into a Docker Sandbox (sbx): by default on a worktree (from the main checkout: ../<repo>-sbx on branch sbx/idle; from a linked worktree: that worktree), or on a new worktree branch or a private clone; the sandbox with the repo's kit and git push over SSH, checks it and prints the line to attach; can carry the user's Claude Code harness; sends a prompt to the agent in a sandbox and returns its reply; tears it down after the merge. Invoke as /sbx, /sbx <type>/<name>, /sbx --clone, /sbx harness, /sbx ask <name> <prompt>, /sbx --done <name>. Background: engineering-standards references/agent-sandbox.md."
disable-model-invocation: true
---

# Sandbox (`/sbx`)

Named `sbx`, not `sandbox`: Claude Code's built-in `/sandbox` (the native sandbox settings) wins over a plugin skill of the same name, so `/sandbox --stack` fails with `Unknown subcommand`. Always tell the user to type `/sbx …`.

Set up a Docker Sandbox (`sbx`) so the user can run Claude Code inside it on a branch of this repo. Claude prepares and checks everything; the user only types the final `sbx run --name …` line in a terminal, because that opens an interactive session Claude cannot drive.

The script is `<this skill>/scripts/sandbox.sh`. Its lines start with `OK`, `WARN`, `FAIL`, `INFO` or `ATTACH`. Never run `sbx run` or `sbx login` yourself; both are interactive.

Argument `$ARGUMENTS`, one of:

- empty (the default): one sandbox on one worktree. From the main checkout: the worktree `../<repo>-sbx` on the idle branch `sbx/idle` (cut from the base branch, no upstream, never pushed) and the sandbox `claude-<repo>-sbx`, both reused when they exist; issues then get their own branches inside it. From a linked worktree: that worktree, on the branch checked out there. Never the main checkout itself. Do not ask for a branch name
- `<type>/<short-name>`: new worktree on a new branch, plus its sandbox (parallel work next to the current checkout)
- `--clone`: a sandbox on a private clone of the repo, nothing on the host checkout changes
- `--done <sandbox-name>`: tear down after the work is merged
- `harness`: build or refresh the personal harness kit (Harness below)
- `ask <sandbox-name> <prompt>`: send a prompt to the agent in that sandbox and show its reply (Ask the agent in a sandbox below)
- `--stack` added to any of the above: the agent will run the Docker stack and its integration tests inside the sandbox (its own Docker engine). The sandbox gets a 40 GB Docker disk and 12 GB memory (`--docker-size`, `--memory` to change); sizes are fixed at creation
- `--recreate` added to any of the above: rebuild an existing sandbox (needed after a kit change)
- `--no-git-auth` added to any of the above: skip the git push setup below; `git push` then runs on the host
- `--host-key '<alg> <base64>'`: the git server's SSH host key, verified out of band (first two fields of its `/etc/ssh/ssh_host_ed25519_key.pub`)
- `--no-harness` added to create: a bare Claude Code without the user's harness kit

## Set up

1. **Preflight.** `bash <this skill>/scripts/sandbox.sh preflight`. A stopped daemon is started by preflight itself (`OK daemon was stopped: started it`). On `FAIL`, stop and give the user the one fix from the output: install sbx, a daemon that would not start (`sbx daemon status`), or `sbx login` in their own terminal (device code in the browser, confirm promptly). Continue when preflight passes. Its harness line: `INFO no Claude Code harness kit` or `WARN … stale` / `new since the last selection`: run the Harness flow below **before creating** (one question, "Build the harness kit first" recommended; skip only on the user's no or `--no-harness`). Kits are fixed at creation: adding the harness later takes `sbx kit add`, which recreates the container and ends a running session. Without it the sandbox gets a bare Claude Code.
2. **Branch name** (only for `<type>/<short-name>`): the same rules as `/branch`: `<type>` is a commit type of the engineering-standards profile, `<short-name>` lowercase kebab-case; propose a correction and ask once if needed. Base branch: the one the repo's CLAUDE.md names; otherwise the script uses `develop` if it exists, else the remote default. Pass `--base <branch>` when the CLAUDE.md names one.
3. **Create.**
   - Default (no argument): `bash <this skill>/scripts/sandbox.sh create`. From the main checkout it creates or reuses `../<repo>-sbx` on `sbx/idle` (pass `--base <branch>` as below); a folder of that name that is not a worktree of this repo is refused. From a linked worktree it mounts that worktree. `--path <dir>` mounts a given checkout; `--path` on the main checkout is the only way to mount it directly, and `check` then warns about it, so offer it only when the user insists.
   - New branch: `bash <this skill>/scripts/sandbox.sh create --branch <type>/<short-name> [--base <branch>]`. The worktree goes next to the main checkout as `../<repo>-<short-name>`.
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
5. **No kit** (exit code 3, `FAIL no sandbox kit`): the repo has no `.sbx/<name>/spec.yaml`. Offer to write one from engineering-standards `references/sbx-kit.md` (its template, or the minimal kit for a repo without a stack, plus a `verify.txt`; then the audit in `references/agent-sandbox.md`), commit it on the repo's base branch with the owner's agreement, and run step 3 again. Do not invent network rules: derive them from the repo's MCP servers, package managers and the services its tests call.
6. **Read the check** the script prints after creating (or run `sandbox.sh check <name>` for an existing sandbox):
   - `git in sandbox: ## <branch>` must be `OK`.
   - `WARN kit tool fails in sandbox: <command>`: a line of the kit's `verify.txt` fails inside, usually an install step whose download was blocked. Read the `network: blocked` lines next to it, add the host to the kit's allow list, commit on the base branch with the owner's agreement, and rerun with `--recreate`.
   - `WARN network: blocked <host>`: the policy refused a request from this sandbox. Add the host to the kit only if the work needs it. `INFO … now in the kit's allow list` is an entry from before the last `--recreate` (the log outlives the sandbox); ignore it.
   - `OK sbx/idle fast-forwarded to <base>`: a reused idle worktree picked up the base branch (e.g. a kit fix), so `--recreate` carries it. `WARN sbx/idle … not fast-forwarded`: local changes or diverged; show the user the printed command, never reset it.
   - `WARN env … kit says …`: the sandbox is older than the kit; rerun with `--recreate`.
   - `WARN host service … nothing listening`: a service the kit points at is not running on the host. Name the host command that starts it (from the repo's CLAUDE.md), for the user to run; the sandbox itself is fine.
   - `WARN host service … blocked by policy`: the port is missing from the kit's allow list.
   - `WARN branch: <base> has N commit(s) touching the kit, … that this branch lacks`: the branch was cut before sandbox setup (kit, compose overlays, Taskfile tasks, CLAUDE.md) reached the base, so the agent inside would improvise around tasks it cannot see. Offer to merge the base branch into it before attaching; never merge without the user's agreement.
   - `WARN sandbox <other> also mounts <worktree>`: a second sandbox works in the same worktree, so two agents overwrite each other's files. On create this is `FAIL sandbox <other> already mounts <worktree>` with exit code 6 and nothing is created: offer to attach to that sandbox instead. Either way the fix is the printed `sbx rm <other>`, once its work is committed and pushed (check `git status` and `git log @{upstream}..` in that worktree with the user first).
   - `WARN sandbox <name> mounts the main checkout <path> directly, not a worktree`: that sandbox's branch switches and commits change the host's own checkout. Ask the user to make sure its work is committed and pushed, then hand over the printed `sbx rm <name>`, and move the work to a worktree (`/sbx <type>/<name>`). `/sbx` creates such sandboxes only with an explicit `--path <main checkout>`; otherwise it is an older sandbox.
   - `WARN sandbox … already exists`: kit and mounts are fixed at creation; offer `--recreate` if the kit or mounts changed, otherwise just attach.
   - A new worktree has no ignored files (`.env`, decrypted secrets, local settings). If the repo needs them, name which ones, and copy them from the main checkout once the user agrees; they are then readable inside the sandbox.
   - `WARN host key … from ssh-keyscan (trust on first use)`: show the fingerprint and ask the user to compare it with the server's (`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` on the server, or the fingerprint the git host publishes). On a mismatch: `sandbox.sh done <name> --force` and create again with `--host-key`. `OK host key … from your known_hosts` means the user's machine already trusts it.
   - `WARN ssh-agent holds no key` / `no ssh-agent reachable`: before attaching, `ssh-add ~/.ssh/<key>` in the terminal the user attaches from (`ssh-add -l` lists it). The agent is forwarded at attach time; without a key, push inside fails with `Permission denied (publickey)`.
   - `WARN git: no SSH host key for <host> in the sandbox` (a sandbox created before this, or with `--no-git-auth`): the printed `sbx kit add <name> …` line adds the kit without losing work. It recreates the container: a running session ends, kit volumes and session state stay, resume with `claude --continue`. Sandboxes too old for `sbx kit add` are refused; then `--recreate`. Needs the kit source allowed (step 4).
   - `WARN git over HTTPS to github.com needs the github secret`: the user runs `sbx secret set github --command 'gh auth token'` (or `sbx secret set github` and pastes a token).
   - `WARN git host API: no gateway MCP server for <host>`: the agent can push but cannot read merge request or pipeline status, so it cannot move its issue to review on a green pipeline. Hand the user the printed `sbx mcp add` (OAuth in their browser, interactive) and `sbx mcp load` lines, and enable the server in the harness selection so a recreate keeps it. Skip when the repo's workflow never asks the agent to check pipelines, or the `gitlab`/`github` kit is used. The gateway is managed with `sbx mcp`, never `docker mcp`.
   - `WARN harness: not in sandbox` / `older than the kit`: the printed `sbx kit add <name> <kit>` brings it in without losing work (recreates the container, like the git kit). `WARN harness install: …`: a marketplace or plugin failed inside; see Harness, troubleshooting.
   - With `--stack`: `WARN no compose overlay` means containers inside will not reach external services. Offer to add the overlay from engineering-standards `references/agent-sandbox.md` (Stack inside the sandbox) and the external hosts to the kit, committed on the base branch with the owner's agreement.
7. **Hand over** in a short block:
   - The attach line from `ATTACH:` alone in a code block, for a terminal (not with `!`, it is interactive). The first start inside may ask for `/login`.
   - Where it runs: worktree folder and branch (by default `../<repo>-sbx` on `sbx/idle`; the agent switches to a new branch per issue there, the main checkout stays on its branch); commits made inside land on that branch on the host at once.
   - The split, briefly. Without `--stack`: inside the sandbox the agent edits, lints, type-checks and runs unit tests; the Docker stack, migrations and end-to-end tests run on the host, and a stack started from a worktree uses the same compose project and database as the main checkout unless started with its own `-p` and ports. With `--stack`: the agent builds, starts and tests the stack inside the sandbox with the overlay (the commands from the repo's CLAUDE.md); the first build takes minutes, later test rounds are fast, and the host stack is untouched.
   - Git: with the git setup `OK`, the agent pushes and pulls inside with plain `git`; first test inside: `ssh -T git@<host>` (SSH) or `git ls-remote origin`. Otherwise `git push` runs on the host.
   - Back later: the same `sbx run --name …` line. Done: `/sbx --done <name>`.
   - For an unattended task: Hand over an autonomous task, below.

## Hand over an autonomous task

`sbx run claude` starts Claude Code with `--dangerously-skip-permissions` (Docker's default for the `claude` agent; passing a bare word after `--` drops it). The sandbox is the main place for unattended coding: permissions are open, the boundary is the sandbox. Depth: engineering-standards `references/autonomous-runs.md`.

**Ask first, once.** Before handing over an autonomous task, ask the human with AskUserQuestion where it runs: this sandbox on its worktree branch (recommended), a supervised host session, unattended on the host in auto mode (only on explicit acceptance: real host files, credentials, network), or not autonomously. Never decide alone. Ask at launch only; inside the sandbox session launched for the task, an active `/goal` or a goal text carrying the approval line, the agent does not ask again and does not call AskUserQuestion at all: it decides within the spec, notes it, reports open questions, and stops cleanly when blocked.

**Use it** for a task with a verifiable end state, a written spec or issue, in a worktree sandbox. **Don't** for exploratory work, a task without a runnable check, or anything that needs production access.

**The goal line** to fill in:

```text
/goal <outcome> is done per <spec path or issue>. Autonomous run approved by <human> on <date>: sandbox <name>, branch <branch>. Proof: `<check command>` exits 0 and its output is shown; `git status` is clean after a commit per finished step. Constraints: only files under <paths> change; no new dependencies without noting them; no edits to tests to make them pass. Do not ask questions; decide within these constraints and note the decision. Stop after <N> turns or when blocked, and report what is done, the evidence, and open questions.
```

- **Proof:** the evaluator reads only the transcript and runs nothing, so the check's output must be printed. Use the repo's real check command (CLAUDE.md, Taskfile); with `--stack`, the integration tests.
- **Approval line:** the recorded decision from the question above, so the run never asks again.
- **Constraints:** what must not change on the way; they stop the agent from passing by weakening the check.
- **Stop after N turns / when blocked:** bounds the loop; the final report is what the human reads.

**Start it.** In the attached session, paste the line. Headless (derived from the docs, not tested here): `sbx run --name <name> -- -p "/goal …" --output-format stream-json --verbose > goal.log` (arguments starting with a flag are appended after the default flags). `/goal` shows status, `/goal clear` stops it; it survives `claude --continue`.

**Guardrails, because permissions are open:**

- The workspace is a bind mount of real host files: use a worktree branch, never the main checkout, and commit per finished step. Checkpoints don't capture Bash changes; commits are the rollback points.
- Network allowlist from the repo's kit, no production secrets in the sandbox (engineering-standards `references/agent-sandbox.md`).
- `/goal` is a Stop hook: it needs hooks enabled (not with `disableAllHooks`) and a trusted workspace.
- Optional: before the final report, a reviewer subagent checks the diff against the spec and reports only correctness gaps (bugs, missing requirements, broken contracts, security).

**Review afterwards:** read the final report and its evidence; `git log` and `git diff <base>...` of the branch; run the check once on the host (or in a fresh sandbox); then open the pull request, split per the size guide. The human reviews the diff before merge.

## Ask the agent in a sandbox (`ask`)

`sandbox.sh ask <name> "<prompt>"` runs one headless turn of Claude Code inside the sandbox (`sbx exec -i <name> claude -p`, prompt over stdin) and prints `OK session <id> · <turns> · <cost>`, then `REPLY:` and the agent's answer. The session id is kept on the host (`${XDG_STATE_HOME:-~/.local/state}/sbx-ask/<name>.session`), so the next `ask` resumes it with `--resume` and the agent remembers the conversation. This is how a host session or orchestrator gives a sandboxed agent work and reads the result, local or in the cloud. Background and other routes: engineering-standards `references/agent-sandbox.md`, Reach the agent from the host.

- `--new` starts a new session (new task, or context grew large). `--read-only` runs it in plan mode: it reads and answers, edits nothing. `--max-turns N` and `--timeout 60m` (default) bound the turn. `--json` prints Claude Code's JSON result (fields `result`, `session_id`, `is_error`, `total_cost_usd`) for scripts. `--cloud` targets a cloud sandbox by ID or name (`sbx --cloud ls`; untested here). Prompt from stdin when none is given or `-`.
- Edits run with open permissions (`bypassPermissions`), like `sbx run claude`; the sandbox is the boundary. Before a task that changes files, the same Ask first as Hand over an autonomous task applies; put the task, the check command and the approval line in the prompt.
- Exit 7: another `ask` to the sandbox still runs (one at a time per sandbox), or an interactive session runs there and the prompt is not `--read-only`. Two agents in one worktree overwrite each other's files: wait, ask read-only, or let the attached session do it.
- `WARN workspace not trusted inside`: Claude Code inside ignores the repo's `.claude/settings.json` permissions and hooks (a `/goal` needs hooks). The user attaches once (`sbx run --name <name>`) and accepts the trust dialog.
- `FAIL no reply … not logged in`: the user attaches once and runs `/login`; `ask` uses the login stored in the sandbox.
- Each `ask` is a full turn that is billed: keep follow-ups short, and use `--new` when the earlier conversation no longer matters.
- `sbx exec` starts a stopped sandbox; it stays running afterwards (`sbx stop <name>`).

## Harness (`harness`)

The sandbox's Claude Code starts bare: no plugins, no user CLAUDE.md, default settings. `sandbox.sh harness` builds a personal kit (v2 mixin) from the user's host setup at `${XDG_CONFIG_HOME:-~/.config}/sbx-kits/claude-harness/`, outside any repo (never commit it). `create` then adds it automatically, with `--skills off` (the kit carries the chosen skills) and `--static-mcp <chosen servers>`. Background: engineering-standards `references/agent-sandbox.md`, Claude Code harness in the sandbox.

1. `bash <this skill>/scripts/sandbox.sh harness`. The first run (and any run that finds new candidates) writes `harness.selection.json` next to the kit, prints it as `TABLE` lines (`[on ]`/`[off]`, `NEW`, a reason for default-off items) and exits 5 without building anything.
2. **Ask the user what to leave out.** Show **every** item from the `TABLE` lines, never a subset: one numbered list per category (marketplaces, plugins, skills, MCP servers, files, settings), numbering running on across categories, each line `N. [on]/[off] name`, plus `NEW` and the reason for default-off items. AskUserQuestion holds at most 4 options per question, too few for a plugin list, so do not put items into options. Ask one single-select question instead: "Build with these choices" (recommended), "I'll edit the file myself" (give the path of `harness.selection.json`, wait, then continue at step 4), and say in the question that "Other" takes the numbers to switch, e.g. `3 7 12`. Only `NEW` items need a decision on later runs; earlier decisions are kept, but still list everything so the user can change them.
3. Edit `harness.selection.json`: set `"enabled": false` (or `true`) per the answers. Never add secrets; `networkAllow` takes extra host names only (see troubleshooting).
4. `bash <this skill>/scripts/sandbox.sh harness --yes` builds the kit: `OK … N plugin(s) …`, `INFO … left out: …`. Relay:
   - `WARN private GitHub marketplaces … github secret`: the user runs `sbx secret set github --command 'gh auth token'`.
   - `WARN MCP server <name> is selected but not registered with sbx`: MCP configs are not copied (they hold tokens). The user registers it on the host with `sbx mcp add` (credentials stay on the host), then reruns step 4; registered servers reach the sandbox through the sbx MCP gateway via `--static-mcp`. MCP servers of a plugin come and go with the plugin.
   - `FAIL local kits are disabled`: the printed `sbx settings set kit.allowLocalKits true`, for the user's terminal.
5. New sandboxes get it on create. Existing ones: `sbx kit add <name> <kit-dir>` (recreates the container, keeps state). `check` reports a stale kit, new candidates and a sandbox older than the kit.

What it carries: an "Inside a Docker Sandbox" section appended to the sandbox's `CLAUDE.md` (pointer to `references/agent-sandbox.md`, tools in containers, `~/.local/bin` on PATH, memory stays on the host, report `Host key verification failed` instead of trusting a scanned key), always, even when the host's `CLAUDE.md` is left out; marketplaces (`claude plugin marketplace add`) and enabled plugins (`claude plugin install --scope user`) as the agent user at creation; `~/.claude/CLAUDE.md`, user agents, commands and output styles; the status line script; selected skills; an allowlist of settings keys merged into the agent's existing `settings.json`. Never: credentials, `~/.claude.json`, history, projects or memory, `env`, `permissions`, `hooks`, MCP configs. Files that look like they hold a secret are refused.

Troubleshooting: `WARN harness install: marketplace … SSH host key is not in your known_hosts`: Claude Code fell back from HTTPS to SSH after the HTTPS clone failed, usually git submodules on a host the kit does not allow, or a very large clone. `sbx policy log <name>` names the host; add it to `networkAllow` in the selection, or leave the marketplace off (marketplaces without an enabled plugin are off by default). A plugin whose install runs a marketplace-declared command is not confirmed automatically (no `-y`); it shows up as failed and is installed by hand inside.

## Tear down (`--done <name>`)

`bash <this skill>/scripts/sandbox.sh done <name>`. For a worktree it refuses while there are uncommitted changes or unpushed commits; for a clone it refuses until the agent's work is fetched (`git fetch sandbox-<name>`, then branch or merge it). Show the refusal and its fix; use `--force` only when the user confirms the work may be discarded. It removes the sandbox, the worktree and the branch if merged, and never the main checkout.

## Rules

- One sandbox per worktree, and none on the main checkout (plain `/sbx` makes a worktree for that reason). Two agents in one worktree overwrite each other's files. `create` refuses a worktree another sandbox already mounts (exit 6), and `check` compares every sandbox's workspaces, not just the named one's, so a stale sandbox on the same worktree or the main checkout shows up as a `WARN`.
- Never mount the host Docker socket; never put secrets into the kit or the command line.
- The harness kit is personal: it stays outside every repo, and it is rebuilt from the user's host config, never edited by hand except `harness.selection.json`.
- Never mount `~/.ssh` or copy a private key into a sandbox; SSH goes through the forwarded agent. For git over HTTPS to a host other than github.com, no custom secret, `insteadOf`, `http.extraHeader` or credential helper: they cannot work through the proxy or put the token inside.
- Language: mirror the user's; commands and branch names in English.
