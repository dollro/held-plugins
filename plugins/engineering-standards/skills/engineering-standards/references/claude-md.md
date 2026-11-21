# CLAUDE.md and documentation structure

Reference structure, taken from a repo where it works well in practice (a multi-component app with a desktop client and a web app). The section shape is the standard; the example lines are illustrations.

## Principles

- **Read docs before code.** The root CLAUDE.md opens with this rule: before changing an area, read the matching `docs/` page, then the component CLAUDE.md, only then the source. Docs hold decisions that are not visible in code.
- **CLAUDE.md is short.** Root around 80 lines, component files around 40 to 60 (Anthropic's ceiling is 200 lines per file). Anything longer is documentation and moves to `docs/`. A bloated CLAUDE.md gets its real rules ignored.
- **The pruning test.** For each line ask: would removing it cause the agent to make mistakes? If not, cut it. If the agent already does it right without the line, delete the line or turn it into a hook. Prune regularly, review it when things go wrong, and check that a change actually shifts behaviour.
- **Only what an agent cannot infer.** Commands, where things must run, hard constraints, branch and commit rules, where plans go. Not a tour of the code, not a feature list, not a changelog.
- **One fact, one place.** CLAUDE.md points to `docs/` instead of repeating it.
- **Must always happen → hook, not CLAUDE.md.** CLAUDE.md is advisory; a hook runs every time. Formatting after edits, blocked paths, "the check passes before you stop" belong in `.claude/settings.json` hooks (Stop-hook pattern in `autonomous-runs.md`).
- **Needed sometimes → skill, not CLAUDE.md.** CLAUDE.md loads every session; domain knowledge or a workflow used now and then goes into a skill (`.claude/skills/<name>/SKILL.md`), which loads on demand. Rules for part of the tree go into path-scoped `.claude/rules/`.
- **`@imports` organise, they don't shrink.** `@docs/testing.md` or `@AGENTS.md` pulls a file in at launch (relative to the importing file, up to four hops; inside backticks it stays literal). It keeps one source for several tools, but the imported text still costs context every session; use a plain pointer ("see `docs/testing.md`") for anything not needed every time.
- **Emphasis sparingly.** `IMPORTANT` on the one line the agent keeps skipping; on many lines, none stands out. No all-caps prose.
- **Tracker plans, `docs/` is current, `plans/` is disposable.** Plans, open questions and decisions live on the issue in the team's issue tracker. `docs/` always describes the code as it is now. `plans/` holds temporary files and can be deleted at any time without losing code, documentation or a decision.

## Root CLAUDE.md

Sections in this order:

| Section | Content | Example line |
|-|-|-|
| `# CLAUDE.md — <Project>` | Title | |
| `## Read Docs Before Code` | The rule above, naming `docs/` and the component CLAUDE.md files | "Before modifying an area, read the matching `docs/` page first, then the component CLAUDE.md." |
| `## Project` | Two or three sentences: what it does, components, stack with versions | "Electron client captures audio; Django 5 + FastAPI + Vue 3 web app … PostgreSQL 17, Redis 7.4." |
| `## Commands` | The task runner commands for daily work, and where things must run | "All webapp work runs inside Docker — never run pytest locally." |
| `### Secrets & env files` | How secrets are edited and kept out of git (only if the repo has secrets) | Encrypted env files, committed `.example` templates, a pre-commit hook that blocks plaintext |
| `## Testing` | Two tables: suites that run in CI, suites that run locally only, each with the command to run it locally | `\| Linting (pre-commit) \| pre-commit run --all-files \|` |
| `## Constraints` | Hard rules: package managers, size limits, lint command | "`pnpm` for JS deps — never npm or yarn." "Max file: 800 lines. Max function: 100 lines." |
| `## Git` | Branch model and commit format | "`main` → `develop` → `feat/*`, `fix/*`, `chore/*`"; "`<type>(<scope>): <subject>`" |
| `## Planning` | Where plans live (the issue tracker) and that `plans/` is only for temporary files | "Plans and decisions go on the tracker issue. `./plans/<branch-name>/` is for temporary files only, not authoritative." |
| `## Agent practices` | One line pointing at the live official guidance as recommended reading; the repo's own rules win | "Recommended reading: https://code.claude.com/docs/en/best-practices (live; this file and the repo's standards take precedence; raise real conflicts with the team)." |

## Sections for repos where agents work

When agents (a sandboxed one, a host session or both) take issues from the tracker, the root CLAUDE.md carries three more sections, because agents read CLAUDE.md every session and a skill loads only when it triggers. Concrete names come from the profile (E5); the rationale is in `autonomous-runs.md` (sections 9 and 10) and `agent-sandbox.md`.

| Section | Content |
|-|-|
| `## Sandbox` | One generic sandbox worktree and its attach line; issues worked one after another in it; per issue a fresh branch from the integration branch; no merging by the agent; how the agent reads pull request and pipeline status (which MCP server) and what to do when it is missing |
| `## Git` (addition) | Trailer `Refs: <KEY>-<n>` on every commit that belongs to an issue |
| `## Issue Tracker` | Tracker and its tool prefix, project key; columns selected by state type, never by name; the Worker field and its names; the "grab your issue" procedure; what to do when the tracker is unreachable |

Template (replace the placeholders; keep it this short):

```markdown
## Sandbox

- **One generic sandbox:** worktree `../atlas-sbx`, sandbox `claude-atlas-sbx` (attach: `sbx run --name claude-atlas-sbx`). Issues are worked one after another inside it, never in parallel.
- **Per issue:** `git fetch origin && git switch -c <type>/acme-<n>-<short-name> origin/develop`; commit and push only that branch, open a pull request into `develop`.
- **No merging by the agent:** never merge, never push to `develop` or `main`, never remove Draft. After a review asking for fixes: push them, wait for green, reply "Fixes applied in <commit>" under the review comment.
- **Pipeline status:** read via the <git host> MCP server. If it is missing, name it and hand the human the command to add it.
- When the pull request is open and green, move the issue to `In Review` and continue with the next issue.

## Git

When a commit belongs to a tracker issue, add a trailer line `Refs: ACME-<n>`.

## Issue Tracker

<Tracker> (`mcp__<tracker>__*` tools) is the issue tracker, project key `ACME`.

- Before starting, find the matching `ACME-<n>` issue; create one for non-trivial work that has none.
- Move issues by the column's state type (`started`, `completed`, `canceled`), never by column name.
- **Worker field:** the owner is assignee; the custom field `Worker` names the agent: `atlas` (sandbox, `$SANDBOX_NAME` set) or `host`. Work only on your own issues; no Worker means the owner hands it out. New issues get issue type `<id>` and a Worker; work needing both agents is two issues.
- **"Grab your issue":** search by your Worker name, confirm the field exactly, drop completed, canceled and blocked issues, skip `In Review` unless its review asks for fixes, take the highest priority (a started one first). Say which and why.
- Tracker unreachable: say so, continue, list the owed updates in the final message.
```

## Component CLAUDE.md

One per component directory (`client/CLAUDE.md`, `webapp/CLAUDE.md`):

| Section | Content |
|-|-|
| `# CLAUDE.md — <Project> <Component> (\`<dir>/\`)` | Title with the directory |
| One paragraph | What the component is and how it talks to the others |
| `## Commands` | Component commands (install, dev, build, test, package) |
| `## Configuration` or `## Access Points` | Config and env, local URLs and ports as a table |
| `## Key Constraints` / `## Key Patterns` | Rules and non-obvious mechanisms of this component, each pointing to its `docs/` page or spec; known violations named ("exceeds 800-line limit — needs refactoring") |
| `## Docs` | One line pointing to the component's `docs/` folder |

## Documentation

| Place | Holds | Authoritative |
|-|-|-|
| `docs/` | The code as it is now: architecture, decisions, how components work and talk, setup, CI/CD, security. One folder per component, built as a site (e.g. MkDocs Material) with link validation. No dated specs or plans | Yes, always current |
| `docs/index.md` | Architecture overview in a few paragraphs, recent features with links, and a documentation guide: one table per component, `\| Document \| Description \|` | Yes |
| Each `docs/` page | Starts with a "Related docs" block linking its neighbours, then the content | Yes |
| Issue tracker (e.g. Linear, GitLab issues) | Plans, open questions, decisions and discussion per issue | Yes, has priority over anything in `plans/` |
| `plans/<branch-name>/` | Temporary files for one branch: scratch notes, intermediate results; the plan only where no tracker is used or connected. Branch `/` becomes `-` (`feat/transcript-log` → `plans/feat-transcript-log/`). Agents read PRD and spec from the tracker, not from a copy here | No; disposable, safe to delete |
| CLAUDE.md | Commands, constraints, pointers | Yes, for how to work in the repo |

Keep the docs build in the repo's checks so broken links fail early.
