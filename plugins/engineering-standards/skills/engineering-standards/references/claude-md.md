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
