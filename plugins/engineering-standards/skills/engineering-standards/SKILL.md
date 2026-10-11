---
name: engineering-standards
description: "Standards for how code gets into a repo: small reviewable pull requests (size check, split), CLAUDE.md structure, where plans and docs live (tracker, docs/, disposable plans/), agent sandboxes (sbx, native sandbox, dev containers) and unattended agent runs (checks, Stop hook, /goal, headless). Use when opening, splitting or reviewing a PR, writing a CLAUDE.md, setting up a repo or sandbox, letting an agent run on its own, or asking how the team builds software. Not for cutting a PRD into issues (prd2issues)."
---

# Engineering Standards

This skill has two parts. **This file** is the method and is organisation-agnostic. **`references/profile.md`** is the organisation profile: where things live, which tools are used, what is still open. **`references/claude-md.md`** is the CLAUDE.md and documentation structure both build on.

**Read `references/profile.md` before any job below.** Read `references/claude-md.md` before writing or reviewing a CLAUDE.md or a `docs/` tree. Read `references/agent-sandbox.md` before setting up or debugging an agent sandbox. Read `references/autonomous-runs.md` before letting an agent run unattended.

**These standards win; the official docs are a check.** Anthropic's Claude Code docs change over time. When setting up a repo, a CLAUDE.md, a sandbox or an unattended run, look up the current pages listed in `references/sources.md` (best practices, `/goal`, hooks, skills, sandboxing). Follow this skill. If the docs now contradict it in a way that matters, tell the user what differs and let them decide; minor differences go into the final report as a note.

Six jobs: **implement an issue**, **size** a change into reviewable pull requests, **write or review a CLAUDE.md**, **set up or check documentation**, **work in an agent sandbox**, **run an agent unattended**.

These standards are guide values for most changes, not law. Where a rule is broken on purpose, the pull request says so and why.

## Implement an issue

An issue is cut to become one pull request (prd2issues). A coding agent plans it itself; these rules keep the result reviewable and honest.

1. **Read first:** the issue, the spec it names, the root and component CLAUDE.md, the matching `docs/` page, then the files in the issue footer.
2. **Branch:** the user runs `/branch <type>/<short-name>` (it runs only when the user invokes it); otherwise create the branch with the same naming and its `plans/<branch-name>/` folder.
3. **Plan briefly** (plan mode is enough): steps, files, the existing file to follow (`file:line`), where new imports and types come from (an existing module, never a new duplicate), the trap a competent implementer would fall into here if there is one, and how each step is checked. The plan, open questions and decisions go on the issue in the team's issue tracker (profile), where the team sees them. Open questions that change behaviour go to the person who owns the issue before building; smaller ones become assumptions written into the pull request. Only without a tracker for this repo, or without a connection to it, the plan goes to `plans/<branch-name>/plan.md`.
4. **Build exactly the issue.** Use only paths, imports and commands verified in the repo, never assumed ones. Anything else found on the way becomes a new issue, not part of this pull request.
5. **Prove it,** cheapest check first: lint and types, then unit tests, then integration tests, then manual or end-to-end steps, using only commands and tools that exist in this repo. Run the issue's `Check` command; every "Done when" item is met by a check or a manual step that was actually run. "Reviewed the code" is not a check.
6. **Parallel issues:** if the issue is marked "sync before merge" with another, build against the shared part written in both issues; if it has to change, update the other issue first. Work in its own branch or worktree.
7. **Update `docs/`** where the change alters what a page describes, in the same pull request.
8. **Open the pull request:** size check as below; description with the issue link, what changed, the check commands and their result, assumptions, and what to review first.

## Size a change

A pull request is the unit of review. Agents write code fast; people still have to understand and own every line that goes in. So:

1. **One pull request does one thing** a reviewer can name in one sentence: one issue, one result. Refactoring, formatting and dependency bumps travel in their own pull requests, not inside a feature.
2. **Stay under the profile's size guide** (changed lines and files, generated and lock files not counted). Check before opening: `git diff --stat <base>...HEAD`.
3. **Over the guide → propose a split** before opening, as a short table: pull request, what it does, files, approx. lines, depends on. Typical cuts: preparatory refactoring first, then the behaviour change; data model or migration before the code that uses it; backend before frontend; one vertical slice at a time behind a flag.
4. **Exceptions** need no split, only a line in the pull request description naming the exception: initial check-in of a new repo or component, a complete refactoring or migration that cannot land in parts without leaving the code broken, mechanical changes (renames, moves, formatter runs) kept in a pull request of their own with nothing else in it.
5. **Every pull request** links its issue, says how it was checked (command and result), and lists what the reviewer should look at first.

6. **Keep files and functions within the profile's length limits.** New code that would exceed them is split into modules; an existing violation is named, not fixed inside a feature.

If a single issue keeps producing oversized pull requests, the issue was cut too large: say so, so the next cut is smaller.

## Write or review a CLAUDE.md

Follow `references/claude-md.md`. A CLAUDE.md is an index and a rulebook for agents, not documentation: short, commands and constraints an agent cannot infer from the code, and pointers into `docs/`. Review findings as `section · problem → fix`, missing sections first, then content that belongs in `docs/`, then wording.

## Set up or check documentation

Follow the documentation part of `references/claude-md.md`. Two places, two jobs:

- **`docs/` describes the code as it is now.** Architecture, decisions, how components work and talk, setup, CI/CD, security. It is always current: no dated specs, no history, no plans. What changed is in git.
- **Planning lives in the issue tracker** (profile): plans, open questions, decisions and discussion go on the issue, which always has priority over files in the repo.
- **`plans/` holds temporary files only** (`plans/<branch-name>/`): the engineer's own scratch notes and intermediate results. Agents read issue, PRD and spec directly from the tracker through its connection; a copy of them, and the plan itself, goes to `plans/` only where no tracker is used or no connection to it is available. It is disposable: deleting all of `plans/` must not lose code, documentation or a decision. A decision that should last goes to the issue, and into `docs/` with the pull request that implements it.

A command or hard constraint an agent needs every session belongs in CLAUDE.md, once.

When code changes behaviour that a `docs/` page describes, the same pull request updates that page.

## Work in an agent sandbox

Follow `references/agent-sandbox.md` (sources in `references/sources.md`). Name the sandbox kind first (Docker Sandboxes microVM, Claude Code native sandbox, dev container), because Docker and host access differ between them. When the agent should verify its own work, run the stack inside the `sbx` sandbox (its own Docker engine, a compose overlay for the sandbox proxy and CA, a large Docker disk set at creation); keep a host stack for browser work. A git worktree in a sandbox needs the main repo's `.git` mounted as a second workspace. Never mount the host's Docker socket into a sandbox. One UID writes into the repo, passed explicitly from the Taskfile. The network allowlist and MCP placeholders live in the repo's kit, secrets stay at the proxy or on the host. When a check fails only in the sandbox, read the policy log before changing code. To move work into a sandbox, the user runs `/sbx` (user-invoked only): without arguments it uses the current checkout and branch, with `<type>/<name>` it creates a new worktree branch for parallel work. First time on a machine, `/sbx harness` comes before it: it builds the personal kit with the user's Claude Code setup (plugins, CLAUDE.md, skills), which a sandbox only gets at creation; without it Claude inside starts bare. `/sbx` then creates the sandbox (and worktree), checks them, prints the line to attach and can hand over an autonomous task with `/goal`. To check or migrate an existing repo, run the reference's audit: findings first as `item · finding → fix`, repo changes after the owner agrees, host commands handed to the human.

## Run an agent unattended

Follow `references/autonomous-runs.md`. **Ask first:** before setting a `/goal`, switching to auto mode or skipped permissions, or starting a headless `claude -p` loop or fan-out, ask the human with AskUserQuestion where it runs (sandbox on a worktree branch recommended; supervised host session; unattended host only on explicit acceptance of the risks; or not autonomously), never decide alone, and record the choice in the report. Ask once at launch, never inside a run (sandbox launched for the task, `claude -p`, active `/goal`, or an approval line in the goal text); inside a run, decide within the spec, note it, and report open questions instead of asking. Preconditions: a check the agent runs itself, a self-contained spec written first, isolation, commits as rollback points. Enforce "done" with the check in the prompt, `/goal`, a Stop hook or a reviewer subagent; bound every loop; a person reviews diff and evidence before merge.

## Language

Mirror the user's language. Code, commit messages, pull request titles, CLAUDE.md and `docs/` are in English.
