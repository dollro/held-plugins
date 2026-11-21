---
name: agent-team
description: "Orchestrates parallel coding agents in Claude Code (Agent Teams, worktree-isolated subagents, parallel sessions, or workers in Docker Sandboxes driven from the host with sbx ask): picks the mechanism, classifies parallel safety, writes interface contracts first, assigns file ownership and runs quality gates. Use when the user wants several agents on one build, says \"agent team\", \"parallel build\", \"swarm\", \"run these issues in parallel\", or when a set of issues (prd2issues) or a plan has 3+ independent parts."
---

# Agent Team Orchestration

You are the **lead** coordinating parallel work. Your role is coordination — you do NOT implement tasks yourself. You choose the mechanism, classify what can run in parallel, fix the shared interfaces, compose a specialised prompt per worker, and gate the results.

> **What this skill adds over the built-ins:** Claude Code spawns teammates, keeps a shared task list, delivers messages and runs worktrees. It does not decide *what* is safe to run in parallel, which mechanism fits, or how workers integrate. This skill does: (1) mechanism choice, (2) parallel-safety classification, (3) contract-first interfaces, (4) per-worker specialisation, (5) quality gates before integration.

Facts about Claude Code below were checked against the docs in October 2026. Agent Teams is experimental and changes quickly — when behaviour differs, the current docs (`code.claude.com/docs/en/agent-teams`, `/agents`, `/worktrees`) win; say so.

## Phase 1: Understand the work

1. Read `CLAUDE.md` (conventions, stack, build and test commands).
2. Find the input, in this order:
   - **A cut of tracker issues** (from prd2issues): read the issues through the tracker connection (e.g. Linear or GitHub MCP), or `issues.md` if there is no connection. Each issue is meant to become one pull request; its footer names files, the pattern to follow, a `Check` command, `Blocked by` and `Parallel`.
   - **A plan or feature description** in the conversation or a file.
   - Neither → ask for one. Do not invent the work.
3. Scan the files each piece of work touches. Every claim about the code is one you read.

## Phase 2: Classify what can run in parallel

For every pair of work items that could run at once, decide one of three states. If the issues already carry a `Parallel` line (prd2issues), check it against the code and correct it where wrong.

| State | Test | Consequence |
|-|-|-|
| **Independent** | Different files, and neither uses a type, API, table or config that the other creates or changes | Can run at the same time and merge separately |
| **Sync before merge** | Related logic, or a shared interface both must keep consistent | Can run at the same time, but the shared part is fixed first (Phase 4) and both are reviewed together before either merges |
| **Sequential** | One uses what the other creates, same file changed, ordered migrations | Dependency; never at the same time |

When unsure between independent and sync before merge, choose sync before merge: a wrong "independent" costs a merge conflict or a silent inconsistency, a wrong "sync" costs one joint review.

If almost everything is sequential, or all items hit the same files, say so: parallelism buys nothing here. One agent, or one item after another, is the answer.

## Phase 3: Choose the mechanism

Ask two questions: does each item end in its own pull request, and do the workers need to talk to each other while working?

| Situation | Mechanism | Why |
|-|-|-|
| Several **independent issues**, each its own PR (the usual prd2issues case) | **One agent per issue in its own worktree:** worktree-isolated subagents, `claude --worktree <name>` sessions, or background sessions | Agent Team teammates share one checkout and one branch; separate PRs need separate worktrees |
| **One issue or feature** split by layer (backend / frontend / tests), workers must coordinate on interfaces | **Agent Team** | Shared task list and messaging; file ownership keeps them apart in one checkout |
| Research, review or competing hypotheses (no edits, or edits to disjoint files) | **Agent Team** or plain subagents | Cheapest form of parallelism; a good first use of teams |
| Several **independent issues** that should run **unattended with open permissions**, or on a cloud sandbox | **Sandbox workers:** one `sbx` sandbox per issue on its own worktree, driven by `sandbox.sh ask` (Sandbox workers below) | The sandbox is the boundary instead of permission prompts; the lead gives work and follow-ups and reads the answers from the host |
| One mechanical change across many files (rename, migration) | Built-in batch splitting or a workflow, one worktree per chunk | Not a team problem |

Rules that apply to every mechanism:
- **Size:** start with 3, at most 5 parallel workers. Three focused workers beat five scattered ones. The real ceiling is how many pull requests people can review: more agents add queue, not capacity.
- **Tokens:** cost grows roughly linearly with the number of workers. Say so when proposing a team.
- **Agent Teams prerequisites:** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` and an interactive session (not `-p` / SDK). If either is missing, fall back to worktree-isolated subagents and say so.

Present the choice in a few lines — items, states, mechanism, number of workers — and get the user's go before spawning.

## Phase 4: Fix contracts BEFORE spawning

**This is the most important phase.** For every "sync before merge" pair and every boundary between workers, define the shared part. Where several items need the same new interface, make it a small first task (or issue) that the others depend on; then they become independent.

### Interface contract template
```
## Contract: [boundary-name] (e.g., "API ↔ Frontend")

### Data shapes (concrete, not prose)
// Request
{ userId: string, filters: { status: "active" | "inactive", limit: number } }
// Response
{ users: Array<{ id: string, name: string, email: string }>, total: number }

### Endpoints / function signatures
GET /api/users?status=active&limit=20 → UsersResponse

### Error cases
- 400: { error: "INVALID_FILTER", message: string }

### Assumptions
- Auth token in Authorization header (Bearer); dates as ISO 8601
```

**Quality check:** could two developers build to this contract independently and integrate on the first try? If not, it isn't specific enough.

- Exact shapes, concrete examples, enumerated error cases.
- Cross-cutting concerns (auth, logging, error handling) assigned to exactly one worker.
- Shared types live in one file both sides import.
- With tracker issues: write the contract into both issues, so it survives the session.

## Phase 5: Specialise each worker

Workers load CLAUDE.md, MCP servers and skills like any session, but they **do not see your conversation**. Everything they need goes into the spawn prompt:

1. **Objective** — the issue or task, with its "Done when" checks.
2. **Ownership** — the files and directories they own, and what they must NOT touch. In an Agent Team this is what prevents overwrites.
3. **Contracts** — what they produce and what they consume, pasted verbatim. Deviations go to the lead first.
4. **Pattern and imports** — the existing file to follow (`file:line`), where types and utilities come from.
5. **Domain context** — the relevant project skills or conventions (e.g. `engineering-standards` for implementing an issue). Don't give every worker the same generic prompt.
6. **Checks** — the exact commands, cheapest first (lint and types, unit, integration). Not done until they pass.
7. **Output** — what to report back: what changed, check commands and results, contract deviations, open questions.

For risky or unclear items, require the worker to plan first (plan mode) and review the plan before it edits.

## Phase 6: Spawn and orchestrate

**Before workers run unattended** (worktree agents or sessions in auto mode or skipped permissions, `/goal`, headless loops), ask the user once where they run, per engineering-standards `references/autonomous-runs.md` (sandbox per worktree recommended); never decide alone. Workers inside such a run don't ask: they decide within their contract and report open questions.

- **Agent Team:** create the tasks in the shared task list with their dependencies (sequential items as blocked-by), then spawn named teammates with the prompts from Phase 5. Teammates claim tasks; message them by name. One team per session.
- **Worktree agents / sessions:** one per issue, each on its own branch (`/branch <type>/<name>` naming), each ending in a pull request that links its issue. Never push to the default branch.
- **Sandbox workers:** see Sandbox workers below.

While they run:
- **Wait for workers** — do not implement their tasks yourself.
- **Watch contract deviations** — evaluate a proposed change and relay it to every affected worker before anyone builds on it.
- **Unblock with targeted messages**, not broadcasts.
- **Task status can lag** — if a dependent task stays blocked although its dependency is done, check and update it.
- **Tracker status** — nothing syncs it automatically. Move issues to in progress / in review yourself, or tell the user.
- Don't leave a team running unattended for long; `/resume` does not restore in-process teammates.

### Sandbox workers (`sbx` + `ask`)

One Docker Sandbox per issue, each on its own worktree branch; the lead stays on the host and talks to each worker with `sandbox.sh ask`, one headless Claude Code turn inside the sandbox that resumes the worker's session. Needs the engineering-standards plugin 1.16.0 or later (its `sbx` skill and `references/agent-sandbox.md`, Reach the agent from the host).

**The user sets up, the lead drives.** `/sbx` is user-invoked, and the first start inside needs `/login`:
1. Per issue, the user runs `/sbx <type>/<name>` (worktree `../<repo>-<name>`, sandbox `claude-<repo>-<name>`), attaches once with the printed `sbx run --name …`, runs `/login`, accepts the workspace trust dialog (otherwise the repo's hooks and settings are ignored, `/goal` included) and exits.
2. The lead finds the script: `ls -d ~/.claude/plugins/cache/*/engineering-standards/*/skills/sbx/scripts/sandbox.sh | sort -V | tail -1`.

**Give the work.** The Phase 5 prompt, with the approval line from the question at the start of Phase 6, goes in once per worker:

```bash
bash "$SBX" ask claude-<repo>-<name> --new --timeout 3h --max-turns 200 < worker-<name>.prompt.md
```

Run each as a background command (several sandboxes in parallel, one `ask` per sandbox at a time) and collect the replies; the reply is the worker's final message, so Phase 5's **Output** section decides what comes back. `OK session …` carries turns and cost per call.

**While they run:**
- **Follow-ups and contract changes** go with a plain `ask` to the worker's sandbox: it resumes the same session, so the worker remembers its task. Send them after its turn has ended; a second `ask` to a busy sandbox exits 7.
- **Status without waiting:** the tracker, `git -C ../<repo>-<name> log` and the pull request's checks, from the host. `ask --read-only` answers questions but also waits until the running turn is done.
- **Nobody attaches while a worker runs:** an attached session and an `ask` would be two agents in one worktree. `ask` refuses to edit while a `claude` process runs there (exit 7).
- **A reply with `FAIL`, a timeout or `is_error`:** read the worktree state first (the turn may have finished part of the work), then send one targeted follow-up; do not restart with `--new`, which loses the worker's context.

**Shut down:** after the merge, `/sbx --done <name>` per sandbox (refuses while work is uncommitted or unpushed).

## Phase 7: Verify and integrate

1. **Contract diff** — ask each worker what interfaces it actually implemented; compare both sides; flag mismatches.
2. **Checks** — each item's check commands pass; the system builds and starts.
3. **Fresh-eyes review** — before merge, a reviewer subagent that sees only the diff (not the worker's reasoning) checks each pull request against its issue, spec and contracts; "sync before merge" pairs are reviewed together. The reviewer reports only correctness gaps: bugs, missing requirements, broken contracts, security issues. No style preferences, no speculative hardening or extra abstraction: a reviewer asked for gaps always finds some, and chasing them over-engineers. Fix correctness gaps; anything else is optional and goes to the user, not back to the worker.
4. **Merge one at a time** — rebase on the default branch, let CI run, then the next. This catches what parallel branches could not see.
5. **Happy path and edge cases** from the issues' "Done when" lists.

If something fails, message the worker that owns it.

## Phase 8: Shut down

Ask each teammate to shut down, wait for confirmation, then clean up the team. Remove worktrees that are merged or abandoned. Report per item: pull request, check results, deviations, what is left.

---

## Optional: quality gate hooks

For recurring projects, enforce gates in `.claude/settings.json`:

```json
{
  "hooks": {
    "TaskCompleted": [{ "hooks": [{ "type": "command", "command": "scripts/verify-task.sh" }] }],
    "TeammateIdle":  [{ "hooks": [{ "type": "command", "command": "scripts/check-idle.sh" }] }]
  }
}
```

- **TaskCompleted** — exit code 2 blocks completion and sends feedback (e.g. "tests not passing").
- **TeammateIdle** — exit code 2 sends feedback and keeps the teammate working.
- **TaskCreated** — exit code 2 blocks creating a task (e.g. a task without a check command).

The hook input arrives as JSON on stdin; check the hooks docs for its fields.

---

## Common pitfalls

1. **Agent Team for separate PRs** — teammates share one checkout; use worktrees.
2. **Spawning without contracts** — the #1 cause of integration failures.
3. **"Independent" that isn't** — two items that both touch a shared type or config.
4. **Vague contracts** — prose instead of shapes.
5. **Generic worker prompts** — the worker doesn't know your conversation; give it everything.
6. **Lead implementing** — the lead coordinates and waits.
7. **Orphaned cross-cutting concerns** — each one has exactly one owner.
8. **Too many workers** — start with 3; review capacity is the limit.
9. **Talking to a busy sandbox** — one `ask` at a time per sandbox, none while someone is attached; read git and the tracker instead.
10. **Weak checks** — a worker verifies against its checks; if they are wrong, it solves the wrong problem.

## Orchestration patterns

**Issues in parallel** (prd2issues output) — classify → contract issue first where needed → one worktree agent per independent issue → fresh-eyes review → merge one at a time.

**Parallel specialists** (one feature) — contracts → Agent Team with file ownership per layer → integration check.

**Sandbox fleet** (issues run unattended) — classify → contracts → the user creates one `/sbx <type>/<name>` per issue → `ask --new` with the worker prompt, in parallel → follow-ups by `ask` → fresh-eyes review → merge one at a time → `/sbx --done`.

**Pipeline** — sequential tasks via dependencies; each stage needs the previous output.

**Research → implement** — read-only subagents or a team explore first; findings feed the worker prompts.

**Review swarm** — several reviewers (security, performance, architecture) examine the same diff in parallel and report to the lead; each reports only gaps against the spec or contract in its area, not style.
