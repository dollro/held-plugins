# CLAUDE.md and documentation structure

Reference structure, taken from a repo where it works well in practice (a multi-component app with a desktop client and a web app). The section shape is the standard; the example lines are illustrations.

## Principles

- **Read docs before code.** The root CLAUDE.md opens with this rule: before changing an area, read the matching `docs/` page, then the component CLAUDE.md, only then the source. Docs hold decisions that are not visible in code.
- **CLAUDE.md is short.** Root around 80 lines, component files around 40 to 60. Anything longer is documentation and moves to `docs/`.
- **Only what an agent cannot infer.** Commands, where things must run, hard constraints, branch and commit rules, where plans go. Not a tour of the code, not a feature list, not a changelog.
- **One fact, one place.** CLAUDE.md points to `docs/` instead of repeating it.
- **Tracker plans, `docs/` is current, `plans/` is disposable.** Plans, open questions and decisions live on the issue in the team's issue tracker. `docs/` always describes the code as it is now. `plans/` holds temporary files and can be deleted at any time without losing code, documentation or a decision.

## Root CLAUDE.md

Sections in this order:

| Section | Content | Example line |
|---|---|---|
| `# CLAUDE.md — <Project>` | Title | |
| `## Read Docs Before Code` | The rule above, naming `docs/` and the component CLAUDE.md files | "Before modifying ANY area, read the matching `docs/` page first, then the component CLAUDE.md." |
| `## Project` | Two or three sentences: what it does, components, stack with versions | "Electron client captures audio; Django 5 + FastAPI + Vue 3 web app … PostgreSQL 17, Redis 7.4." |
| `## Commands` | The task runner commands for daily work, and where things must run | "All webapp work runs inside Docker — never run pytest locally." |
| `### Secrets & env files` | How secrets are edited and kept out of git (only if the repo has secrets) | Encrypted env files, committed `.example` templates, a pre-commit hook that blocks plaintext |
| `## Testing` | Two tables: suites that run in CI, suites that run locally only, each with the command to run it locally | `\| Linting (pre-commit) \| pre-commit run --all-files \|` |
| `## Constraints` | Hard rules: package managers, size limits, lint command | "`pnpm` for JS deps — never npm or yarn." "Max file: 800 lines. Max function: 100 lines." |
| `## Git` | Branch model and commit format | "`main` → `develop` → `feat/*`, `fix/*`, `chore/*`"; "`<type>(<scope>): <subject>`" |
| `## Planning` | Where plans live (the issue tracker) and that `plans/` is only for temporary files | "Plans and decisions go on the tracker issue. `./plans/<branch-name>/` is for temporary files only — NOT authoritative." |

## Component CLAUDE.md

One per component directory (`client/CLAUDE.md`, `webapp/CLAUDE.md`):

| Section | Content |
|---|---|
| `# CLAUDE.md — <Project> <Component> (\`<dir>/\`)` | Title with the directory |
| One paragraph | What the component is and how it talks to the others |
| `## Commands` | Component commands (install, dev, build, test, package) |
| `## Configuration` or `## Access Points` | Config and env, local URLs and ports as a table |
| `## Key Constraints` / `## Key Patterns` | Rules and non-obvious mechanisms of this component, each pointing to its `docs/` page or spec; known violations named ("exceeds 800-line limit — needs refactoring") |
| `## Docs` | One line pointing to the component's `docs/` folder |

## Documentation

| Place | Holds | Authoritative |
|---|---|---|
| `docs/` | The code as it is now: architecture, decisions, how components work and talk, setup, CI/CD, security. One folder per component, built as a site (e.g. MkDocs Material) with link validation. No dated specs or plans | Yes, always current |
| `docs/index.md` | Architecture overview in a few paragraphs, recent features with links, and a documentation guide: one table per component, `\| Document \| Description \|` | Yes |
| Each `docs/` page | Starts with a "Related docs" block linking its neighbours, then the content | Yes |
| Issue tracker (e.g. Linear, GitLab issues) | Plans, open questions, decisions and discussion per issue | Yes, has priority over anything in `plans/` |
| `plans/<branch-name>/` | Temporary files for one branch: scratch notes, intermediate results; the plan only where no tracker is used or connected. Branch `/` becomes `-` (`feat/transcript-log` → `plans/feat-transcript-log/`). Agents read PRD and spec from the tracker, not from a copy here | No; disposable, safe to delete |
| CLAUDE.md | Commands, constraints, pointers | Yes, for how to work in the repo |

Keep the docs build in the repo's checks so broken links fail early.
