---
name: engineering-standards
description: "Engineering standards for how code gets into a repo: small reviewable pull requests, the structure of CLAUDE.md files, and where planning and documentation live (issue tracker for plans and decisions, docs/ for the current state of the code, plans/ for disposable temporary files). Sizes a change before a PR and proposes a split, writes or reviews a CLAUDE.md, sets up or checks a repo's documentation. Loaded profile: default (replace references/profile.md with your organisation's). Use whenever someone is about to open, split or review a pull request, sets up a new repo, writes or cleans up a CLAUDE.md, asks where documentation or plans belong, or asks how the team builds software, even if standards are not mentioned. Not for cutting a PRD into issues (prd2issues)."
---

# Engineering Standards

This skill has two parts. **This file** is the method and is organisation-agnostic. **`references/profile.md`** is the organisation profile: where things live, which tools are used, what is still open. **`references/claude-md.md`** is the CLAUDE.md and documentation structure both build on.

**Read `references/profile.md` before any job below.** Read `references/claude-md.md` before writing or reviewing a CLAUDE.md or a `docs/` tree.

Four jobs: **implement an issue**, **size** a change into reviewable pull requests, **write or review a CLAUDE.md**, **set up or check documentation**.

These standards are guide values for most changes, not law. Where a rule is broken on purpose, the pull request says so and why.

## Implement an issue

An issue is cut to become one pull request (prd2issues). A coding agent plans it itself; these rules keep the result reviewable and honest.

1. **Read first:** the issue, the spec it names, the root and component CLAUDE.md, the matching `docs/` page, then the files in the issue footer.
2. **Branch:** start with `/branch <type>/<short-name>`.
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

## Language

Mirror the user's language. Code, commit messages, pull request titles, CLAUDE.md and `docs/` are in English.
