---
name: sandbox
description: "Starts Claude Code in a Docker Sandbox (sbx) for a repo: creates a git worktree on a new branch (or uses the current checkout, or a private clone), creates the sandbox with the repo's kit and the right mounts, checks it from outside (git, kit environment, host services) and hands over one line to attach. Also tears it down after the merge. Use when someone says /sandbox <type>/<name>, /sandbox, /sandbox --clone, /sandbox --done <name>, \"run Claude in a sandbox\", \"sandbox for this branch/worktree\", \"start a sandboxed agent\", \"Sandbox starten\". Background and troubleshooting: engineering-standards references/agent-sandbox.md."
---

# Sandbox

Set up a Docker Sandbox (`sbx`) so the user can run Claude Code inside it on a branch of this repo. Claude prepares and checks everything; the user only types the final `sbx run --name …` line in a terminal, because that opens an interactive session Claude cannot drive.

The script is `<this skill>/scripts/sandbox.sh`. Its lines start with `OK`, `WARN`, `FAIL`, `INFO` or `ATTACH`. Never run `sbx run` or `sbx login` yourself; both are interactive.

Argument `$ARGUMENTS`, one of:

- `<type>/<short-name>`: new worktree on a new branch, plus its sandbox (the usual case)
- empty: a sandbox for the current checkout or worktree
- `--clone`: a sandbox on a private clone of the repo, nothing on the host checkout changes
- `--done <sandbox-name>`: tear down after the work is merged
- `--recreate` added to any of the above: rebuild an existing sandbox (needed after a kit change)

## Set up

1. **Preflight.** `bash <this skill>/scripts/sandbox.sh preflight`. On `FAIL`, stop and give the user the one fix from the output: install sbx, `sbx daemon start -d`, or `sbx login` in their own terminal (device code in the browser, confirm promptly). Continue when preflight passes.
2. **Branch name** (only for `<type>/<short-name>`): the same rules as `/branch`: `<type>` is a commit type of the engineering-standards profile, `<short-name>` lowercase kebab-case; propose a correction and ask once if needed. Base branch: the one the repo's CLAUDE.md names; otherwise the script uses `develop` if it exists, else the remote default. Pass `--base <branch>` when the CLAUDE.md names one.
3. **Create.**
   - New branch: `bash <this skill>/scripts/sandbox.sh create --branch <type>/<short-name> [--base <branch>]`. The worktree goes next to the main checkout as `../<repo>-<short-name>`.
   - Current checkout: `bash <this skill>/scripts/sandbox.sh create` (from inside it), or `--path <dir>`.
   - Clone: `bash <this skill>/scripts/sandbox.sh create --clone`.

   The first creation runs the kit's install steps and can take minutes; say so before starting. For a linked worktree the script mounts the main repo's `.git` as a second, writable workspace automatically.
4. **No kit** (exit code 3, `FAIL no sandbox kit`): the repo has no `.sbx/<name>/spec.yaml`. Offer to write one from the template in engineering-standards `references/agent-sandbox.md` (Kit section, then its audit), commit it on the repo's base branch with the owner's agreement, and run step 3 again. Do not invent network rules: derive them from the repo's MCP servers, package managers and the services its tests call.
5. **Read the check** the script prints after creating (or run `sandbox.sh check <name>` for an existing sandbox):
   - `git in sandbox: ## <branch>` must be `OK`.
   - `WARN env … kit says …`: the sandbox is older than the kit; rerun with `--recreate`.
   - `WARN host service … nothing listening`: a service the kit points at is not running on the host. Name the host command that starts it (from the repo's CLAUDE.md), for the user to run; the sandbox itself is fine.
   - `WARN host service … blocked by policy`: the port is missing from the kit's allow list.
   - `WARN sandbox … already exists`: kit and mounts are fixed at creation; offer `--recreate` if the kit or mounts changed, otherwise just attach.
   - A new worktree has no ignored files (`.env`, decrypted secrets, local settings). If the repo needs them, name which ones to copy or decrypt into the worktree.
6. **Hand over** in a short block:
   - The attach line from `ATTACH:` alone in a code block, for a terminal (not with `!`, it is interactive). The first start inside may ask for `/login`.
   - Where it runs: branch and folder; commits made inside land on that branch on the host at once.
   - The split, briefly: inside the sandbox the agent edits, lints, type-checks and runs unit tests; the Docker stack, migrations, end-to-end tests and `git push` run on the host. A stack started from a worktree uses the same compose project and database as the main checkout unless started with its own `-p` and ports; run one at a time.
   - Back later: the same `sbx run --name …` line. Done: `/sandbox --done <name>`.

## Tear down (`--done <name>`)

`bash <this skill>/scripts/sandbox.sh done <name>`. For a worktree it refuses while there are uncommitted changes or unpushed commits; for a clone it refuses until the agent's work is fetched (`git fetch sandbox-<name>`, then branch or merge it). Show the refusal and its fix; use `--force` only when the user confirms the work may be discarded. It removes the sandbox, the worktree and the branch if merged, and never the main checkout.

## Rules

- One sandbox per worktree. Two agents in one worktree overwrite each other's files.
- Never mount the host Docker socket; never put secrets into the kit or the command line.
- Language: mirror the user's; commands and branch names in English.
