---
name: engineering-standards
description: "Standards for how code gets into a repo: small reviewable pull requests (size check, split), review, merge and release discipline (high-risk review, one merge at a time, release pull request), CLAUDE.md structure, where plans and docs live (tracker, docs/, disposable plans/), agent sandboxes (sbx, native sandbox, dev containers) and unattended agent runs (checks, Stop hook, /goal, headless, rules for several agents on one repo). Use when opening, splitting, reviewing or merging a PR, preparing a release merge, writing a CLAUDE.md, setting up a repo or sandbox, letting an agent run on its own, or asking how the team builds software. Not for cutting a PRD into issues (prd2issues)."
---

# Engineering Standards

This skill has two parts. **This file** is the method and is organisation-agnostic. **`references/profile.md`** is the organisation profile: where things live, which tools are used, what is still open. **`references/claude-md.md`** is the CLAUDE.md and documentation structure both build on.

**Read `references/profile.md` before any job below.** Read `references/claude-md.md` before writing or reviewing a CLAUDE.md or a `docs/` tree. Read `references/review-merge-release.md` before reviewing, merging or releasing. Read `references/agent-sandbox.md` before setting up or debugging an agent sandbox, and `references/sbx-kit.md` before writing or changing a repo's `sbx` kit. Read `references/autonomous-runs.md` before letting an agent run unattended.

**These standards win; the official docs are a check.** Anthropic's Claude Code docs change over time. When setting up a repo, a CLAUDE.md, a sandbox or an unattended run, look up the current pages listed in `references/sources.md` (best practices, `/goal`, hooks, skills, sandboxing). Follow this skill. If the docs now contradict it in a way that matters, tell the user what differs and let them decide; minor differences go into the final report as a note.

Seven jobs: **implement an issue**, **size** a change into reviewable pull requests, **review, merge and release**, **write or review a CLAUDE.md**, **set up or check documentation**, **work in an agent sandbox**, **run an agent unattended**.

These standards are guide values for most changes, not law. Where a rule is broken on purpose, the pull request says so and why.

## Implement an issue

An issue is cut to become one pull request (prd2issues). A coding agent plans it itself; these rules keep the result reviewable and honest.

1. **Read first:** the issue, the spec it names, the root and component CLAUDE.md, the matching `docs/` page, then the files in the issue footer.
2. **Branch:** the user runs `/branch <type>/<short-name>` (it runs only when the user invokes it); otherwise create the branch with the same naming and its `plans/<branch-name>/` folder.
3. **Plan briefly** (plan mode is enough): steps, files, the existing file to follow (`file:line`), where new imports and types come from (an existing module, never a new duplicate), the trap a competent implementer would fall into here if there is one, and how each step is checked. The plan, open questions and decisions go on the issue in the team's issue tracker (profile), where the team sees them. Open questions that change behaviour go to the person who owns the issue before building; smaller ones become assumptions written into the pull request. Only without a tracker for this repo, or without a connection to it, the plan goes to `plans/<branch-name>/plan.md`.
4. **Build exactly the issue.** Use only paths, imports and commands verified in the repo, never assumed ones. Anything else found on the way becomes a new issue, not part of this pull request.
5. **Prove it,** cheapest check first: lint and types, then unit tests, then integration tests, then manual or end-to-end steps, using only commands and tools that exist in this repo. Run the issue's `Check` command; every "Done when" item is met by a check or a manual step that was actually run. "Reviewed the code" is not a check. **A new gate is proven to fail:** seed a deliberate violation for a new lint or type check, run new tests against the old code and watch them fail. A gate that never failed proves nothing.
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

## Review, merge and release

Follow `references/review-merge-release.md`; the rules in short:

1. **High-risk changes get a review pass before merge** (auth, mail, payments, deploy and CI, data migrations), checking behaviour and failure paths. The review lands on the tracker issue; own work is reviewed by a fresh subagent that sees only the diff and the requirements. Check conflicts against what lands first; a stacked pull request is rebased onto the target once its base merges.
2. **The reviewer owns the Draft flag.** The author pushes fixes and replies "Fixes applied in <commit>"; only the reviewer removes Draft, and only non-Draft pull requests merge.
3. **Update a feature branch by merging the target into it,** not by rebasing a branch others or CI already use.
4. **Merge one pull request at a time,** or batch by hand on a temporary branch that CI tests, then fast-forward and push once. Conflicting approved pull requests are never resolved inside the batch, and what lands is exactly what was tested.
5. **No standing release pull request:** open it when the candidate is green, track the release as one tracker issue, describe it with the release template, fast-forward where possible.
6. **Release often.**
7. **Flaky tests are fixed at the cause:** one retry to tell, then an issue with the evidence.

Release mechanics (tags, pipeline, deploy, rollback) belong to the stack's own guideline (e.g. `fullstack-engineering`).

## Write or review a CLAUDE.md

Follow `references/claude-md.md`. A CLAUDE.md is an index and a rulebook for agents, not documentation: short, commands and constraints an agent cannot infer from the code, and pointers into `docs/`. Repos where agents take issues from the tracker also get the reference's Sandbox, Issue Tracker and Git-trailer sections (template there, names from the profile). Review findings as `section · problem → fix`, missing sections first, then content that belongs in `docs/`, then wording.

## Set up or check documentation

Follow the documentation part of `references/claude-md.md`. Two places, two jobs:

- **`docs/` describes the code as it is now.** Architecture, decisions, how components work and talk, setup, CI/CD, security. It is always current: no dated specs, no history, no plans. What changed is in git.
- **Planning lives in the issue tracker** (profile): plans, open questions, decisions and discussion go on the issue, which always has priority over files in the repo.
- **`plans/` holds temporary files only** (`plans/<branch-name>/`): the engineer's own scratch notes and intermediate results. Agents read issue, PRD and spec directly from the tracker through its connection; a copy of them, and the plan itself, goes to `plans/` only where no tracker is used or no connection to it is available. It is disposable: deleting all of `plans/` must not lose code, documentation or a decision. A decision that should last goes to the issue, and into `docs/` with the pull request that implements it.

A command or hard constraint an agent needs every session belongs in CLAUDE.md, once.

When code changes behaviour that a `docs/` page describes, the same pull request updates that page.

## Work in an agent sandbox

Follow `references/agent-sandbox.md`. Name the sandbox kind first (Docker Sandboxes microVM, native sandbox, dev container), because Docker and host access differ. Principles: the agent runs the stack inside the sandbox to verify its own work; the host Docker socket is never mounted; secrets stay at the proxy or on the host; a check that fails only in the sandbox is a policy question before a code question. The user starts sandboxes with `/sbx` (first time on a machine `/sbx harness`); when the user asks Claude to set one up instead, read `../sbx/SKILL.md` (this plugin) and follow it, since that skill cannot be invoked by the model; a host orchestrator talks to a sandboxed agent with `/sbx ask`. To check or migrate a repo, run the reference's audit.

## Run an agent unattended

Follow `references/autonomous-runs.md`. **Ask the human once, at launch,** where it runs (sandbox recommended) before any `/goal`, auto mode, skipped permissions or headless loop; never ask inside a run. Preconditions: a check the agent runs itself, a self-contained spec, isolation, commits as rollback points; "done" is enforced by a check, every loop is bounded, and a person reviews before merge. Several agents on one repo follow the reference's agent rules (one branch per issue, agents never merge, the tracker is the shared state, a `Worker` field routes issues).

## Language

Mirror the user's language. Code, commit messages, pull request titles, CLAUDE.md and `docs/` are in English.
