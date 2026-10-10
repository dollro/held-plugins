# Profile: default

Organisation profile for the skill `engineering-standards`. These are neutral defaults. To adapt the skill to an organisation, replace this file with a profile of the same shape.

## E1. Where code and work live

- **Code:** the organisation's git host (GitHub, GitLab or similar). Check the repo's remote; do not assume one.
- **Issue tracker:** the team's tracker (e.g. Linear, GitHub issues, GitLab issues). Issues, plans, open questions, decisions and discussion live there, on the issue; this always has priority over files in the repo. Every pull request links its issue; one issue is cut so that it becomes one pull request (`prd2issues`). Which tracker a repo uses is stated in its CLAUDE.md; if it is not, ask.
- **Commit messages:** conventional commits, `<type>(<scope>): <subject>`; types feat, fix, docs, style, refactor, test, chore.

## E2. Pull request size

Guide values for a reviewable pull request. Generated files, lock files and pure snapshot or fixture data are not counted.

| | Guide | Above it |
|---|---|---|
| Changed lines | about 400 | Propose a split |
| Changed files | about 20 | Soft warning: the pull request description says why it touches that many places |

The same guide bounds an issue: an issue is cut so that its pull request stays within it (`prd2issues`). Exceptions as in the skill: initial check-in, complete refactoring or migration, mechanical changes in their own pull request.

## E2b. File and function length

| | Maximum |
|---|---|
| Lines per file | 800 |
| Lines per function | 100 |

- **New code** stays within the limits. A file that grows beyond them is split into modules.
- **Existing violations** are named in the component CLAUDE.md under Key Constraints ("exceeds 800-line limit — needs refactoring") and fixed in a refactoring pull request of their own, never inside a feature.
- **Exceptions:** generated code, migrations, test fixtures and data files.
- Every repo's root CLAUDE.md states the limits under `## Constraints`.

## E3. CLAUDE.md and documentation

Structure as in `claude-md.md`. Every repo has a root CLAUDE.md, a component CLAUDE.md per component directory, and a `docs/` folder as the authoritative record.

**Plans and docs:** plans and decisions go on the tracker issue. `docs/` always describes the code as it is now, with no specs subfolder. `plans/<branch-name>/`, created by `/branch`, holds temporary files only, and the plan itself only where a repo has no tracker or no connection to it. PRD and spec stay in the tracker, and coding agents read them there through its connection; a copy goes to `plans/` only where that connection is not available. All of `plans/` is safe to delete.

## E4. Not yet covered

Tech stack and approved tools, test and eval standards, Definition of Done in detail, code review rules, CI requirements, secrets handling. Until a profile adds them, look them up in the repo's own CLAUDE.md, or ask the team; never invent them.
