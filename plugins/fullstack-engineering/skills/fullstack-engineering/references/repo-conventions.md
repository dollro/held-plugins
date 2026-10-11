# Repo conventions in CLAUDE.md

What a repo built on this stack must tell an agent, so that anyone (person or agent) can start, stop, test and deploy it without guessing. The section structure of CLAUDE.md comes from `engineering-standards` (`references/claude-md.md`); this file supplies the stack-specific content.

## What the root CLAUDE.md must cover

| Topic | Must say | Example (reference stack) |
|-|-|-|
| Where things run | That services, tests and package managers run in containers, and what must never run on the host | "Everything runs in Docker through Task. Never run Django, pytest, uv sync or pnpm on the host." |
| First run | The one command that prepares a fresh clone | `task setup` |
| Start | How to start the stack **in the background**, and the URL | `task dev:up` → http://localhost:8000 |
| State and logs | How to see what runs and follow logs per service | `task dev:ps`, `task dev:logs -- django` |
| Restart after config changes | That env file changes need a recreate, not a restart | `task dev:restart -- django` |
| Stop and reset | Stop keeping data; reset deleting data (with a warning) | `task dev:down`, `task dev:reset` |
| Rebuild | When images must be rebuilt | `task dev:build` after Dockerfile or dependency changes |
| Framework commands | Management commands, migrations, dependency locking | `task dev:manage -- <cmd>`, `task dev:makemigrations`, `task deps:lock` |
| Tests | CI suites and local-only suites, each with its command (table) | `task check:lint`, `task check:docs`, `task check:frontend`, `task test:backend`, `task test:e2e`, `task ci` |
| Docs | How to view the docs site | `task docs:serve` |
| Secrets and environments | How env files are edited per environment and where deploy state lives | `task secrets:edit ENV=local\|staging\|production`, `.envs/<env>/deploy.env` |
| Release and deploy | The promotion path in one line | tag → staging → production with `task deploy ENV=…` |
| Constraints | Package managers, size limits, one table owner, HTTP client rule, login rule | see the template's CLAUDE.md |

Component CLAUDE.md files (`backend/`, `frontend/`, `realtime/`) hold the component's commands, access points (admin, Flower, mail catcher, dev servers) and key patterns, each pointing to its `docs/` page.

## Why "in the background"

An agent's shell blocks on a foreground `docker compose up`. Start commands return once services are healthy (`docker compose up -d --wait`); logs are a separate command. The same command then works for people, agents and scripts.

## Applying this to an existing repo

When an agent works in a repo whose CLAUDE.md lacks these topics, or describes commands that no longer exist:

1. **Find the real commands first:** read the task runner file (Taskfile, Makefile, `package.json` scripts, `justfile`) and the compose files, and try the read-only ones (`task --list`, `docker compose ps`). Document what the repo actually has. Never invent targets that do not exist, and do not introduce Task into a repo that uses something else without being asked.
2. **Merge, do not overwrite:** add missing topics to the existing sections (Commands, Testing, Constraints) in the structure of `engineering-standards`; keep the repo's own content and wording; remove only lines that are verifiably wrong (a command that fails or no longer exists).
3. **Keep it short:** commands and rules only; explanations go to `docs/`. Root CLAUDE.md stays around 80 lines.
4. **Same change, named in the hand-back:** the CLAUDE.md update goes into the pull request that needed it, and the hand-back says what was added or corrected.
5. **Missing start/stop commands are a finding, not a reason to build infrastructure:** if a repo cannot be started with one command, say so once (*Repos on another stack*) and propose the smallest fix (e.g. a task or make target wrapping the existing compose command).

## Keeping it current

- A pull request that adds, renames or removes a command updates CLAUDE.md (and `docs/` where the behaviour is explained) in the same change.
- `task --list` (or the runner's equivalent) is the source of truth for names; CLAUDE.md lists the daily ones and points to it for the rest.
