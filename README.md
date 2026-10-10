# held-plugins

A curated marketplace of [Claude Code](https://claude.ai/code) plugins: ways of
working, engineering standards, reference stacks and design skills, so people
and agents work from the same playbook. Covers product management (idea to
issues), delivery (pull requests, parallel agents, review), agentic AI, full-stack
web and desktop apps, UI/UX design systems and financial analysis.

The marketplace is tenant-agnostic: no organisation names or defaults.
Organisation-specific settings live in swappable profile files (see
*Organisation profile* below).

Maintained by Held.

## Install

```bash
# register the marketplace (once)
claude plugin marketplace add dollro/held-plugins

# install a plugin
claude plugin install <plugin-name>@held-plugins
```

Inside a session: `/plugin marketplace add dollro/held-plugins`, then `/plugin`
to browse and enable what you want.

Pull updates with `claude plugin marketplace update held-plugins`.

Skills load on their own when a task matches their description; you can also
call them directly as `/<skill-name>`. Agents are used by asking for them ("let
the fullstack-engineer build …").

## Plugins

### Product management: from idea to issues

| Plugin | What it does |
|---|---|
| `prfaq-vision-builder` | Guided Working Backwards PR/FAQ: a future-state press release plus lean FAQ, to align a team on a vision |
| `product-roadmap-3-layers` | Roadmap in three layers (Business Outcomes, Product & Features, Tech Enablers) in Now/Next/Later, from an interview or a Notion roadmap database |
| `braindump2prd` | Interviews a product manager and turns a feature idea into a plain-language PRD and spec, handed over to the issue tracker |
| `prd2issues` | Cuts a Ready PRD into milestones and a few readable tracker issues, grounded in the actual codebase, each one reviewable pull request with its parallel-safety status |

### Delivery: how work gets built

| Plugin | What it does |
|---|---|
| `engineering-standards` | Small reviewable pull requests, CLAUDE.md structure, where docs and plans live, how to implement an issue, agent sandbox practice (code in the sandbox, stack on the host); `/branch` starts a branch with its `plans/` folder; `/sandbox <type>/<name>` creates a worktree and a Docker Sandbox for it, checks both and prints the one line to attach Claude; `--stack` sizes it so the agent runs the Docker stack and integration tests inside the sandbox itself. Swappable organisation profile |
| `agent-team` | Runs several issues (or one large one) with parallel coding agents: mechanism choice (worktrees or Agent Teams), parallel-safety check, contracts first, quality gates, one PR at a time |
| `brainstorming` | Structured exploration of intent, requirements and design before any implementation |

For review, use Anthropic's `code-review` plugin from `claude-plugins-official`
(parallel reviewers, CLAUDE.md compliance, confidence-filtered findings) and the
built-in `/security-review`; this marketplace does not duplicate them.

### Engineering: reference stacks and agents

| Plugin | What it does |
|---|---|
| `fullstack-engineering` | Guideline and tested reference stack for web apps (Django + optional FastAPI realtime, Vue 3, PostgreSQL, Redis, Celery, Docker, Task, SOPS), login for internal staff (company SSO over OpenID Connect), external users (accounts with MFA) or both, staging and production from the same image; `/fullstack-scaffold` generates a new repo that passes its own CI, the `fullstack-engineer` agent builds features |
| `agentic-engineering` | Standards for production agent systems: LangGraph, Pydantic AI, CrewAI, Langfuse; state, model tiers, validation, human-in-the-loop, evals; the `agentic-engineer` agent builds them |
| `prompt-engineering` | Prompt design, evaluation frameworks and production prompt systems; the `prompt-engineer` agent |
| `electron-dev` | Secure, fast desktop apps with Electron on Forge + Vite + TypeScript: typed IPC, fuses, signing, auto-update, tests; the `electron-developer` agent |

### UI/UX design and frontend

| Plugin | What it does |
|---|---|
| `uiux-design-system` | Design system architecture: component hierarchy, three-tier tokens (DTCG), theming, typography, accessibility (WCAG 2.2) |
| `uiux-design-tailwindv4` | Design systems in Tailwind CSS v4: CSS-first theme, semantic tokens, OKLCH colours, component variants, dark mode |
| `uiux-design-vue3` | Vue 3 skills: Composition API, router, Pinia, composables, testing, debugging |
| `uiux-image2design` | Turns UI screenshots into a design system and screens in Penpot or Figma |
| `uiux-design-penpot` | Designing in Penpot via MCP: tokens, components, prototypes |
| `uiux-design-figma` | Designing in Figma via MCP: variables, auto-layout, component variants |
| `design-parity` | Closes the gap between a design spec and its implementation: screenshot diffs via Playwright or Chrome DevTools MCP, with a fix plan |
| `pencil-pen-generator` | Generates and converts Pencil `.pen` design files |

### Analysis

| Plugin | What it does |
|---|---|
| `equity-research` | Equity research with chance/risk reports, DCF valuation and a recommendation for US-listed stocks |
| `investment-memo` | VC investment memos (seed, Series A) from pitch decks and DD material, scored across team, technology, market, competition, business model and financials |

Versions live in each plugin's `plugin.json` and in `.claude-plugin/marketplace.json`; `/plugin` shows them.

## Workflows

### Idea to merged PR

The product, delivery and engineering plugins are built to chain. Each step
hands a concrete artifact to the next; nothing is written to the tracker or
merged without your confirmation.

```
 PRODUCT                                  ENGINEERING
 prfaq-vision-builder      why, for whom?
        │
 product-roadmap-3-layers  what, in which order?
        │
 braindump2prd             one feature → PRD + spec ──► tracker project
        │
        └────────────► prd2issues   PRD → issues, parallel-safety ──► tracker issues
                              │
                  ┌───────────┴───────────┐
             one issue              several in parallel
       engineering-standards           agent-team
       /branch → plan → build →    one worktree agent per issue,
       check → docs → PR           or a team for one large issue
                  │                       │
                  │   domain skills while building: fullstack-engineering,
                  │   agentic-engineering, electron-dev, uiux-*, prompt-engineering
                  └───────────┬───────────┘
                     review: official code-review plugin,
                     /security-review (+ design-parity for UI)
                              │
                     merge, one PR at a time
```

|#|Step|Plugin|Output|
|-|-|-|-|
|1|Vision (new products, optional)|`prfaq-vision-builder`|One PR/FAQ document: future press release plus lean FAQ|
|2|Order the work|`product-roadmap-3-layers`|Now/Next/Later roadmap: outcomes → features → tech enablers|
|3|Specify one feature|`braindump2prd`|`braindump_final.md` (interview record) → `prd.md` + `spec.md`, handed to the tracker project|
|4|Cut into issues — run in the product repo|`prd2issues`|1–3 issues per result, each one reviewable PR, with files, pattern to follow, check command, `Blocked by` and `Parallel`|
|5a|Build one issue|`engineering-standards`|`/branch` (or `/sandbox <type>/<name>` to build inside a Docker Sandbox) → short plan on the issue → code → checks, cheapest first → `docs/` update → PR|
|5b|Build several issues at once|`agent-team`|Independent issues: one agent each in its own worktree. "Sync before merge" pairs: shared contract first|
|6|Review|`code-review` from `claude-plugins-official`, `/security-review`, `design-parity`|Confidence-filtered findings on the PR (incl. CLAUDE.md compliance); security review; design-vs-implementation diff for UI|

**Principles**

- **One fact, one place.** Goal in the PRD, behaviour in the spec, plan and
  decisions on the issue, current state of the code in `docs/`.
- **Plan just in time.** No upfront plan for a whole feature; each issue gets a
  short plan against the code as it is when work starts.
- **The pull request is the unit.** About 400 changed lines. Review capacity,
  not agent count, limits parallelism — start with three parallel agents.

**Variants**

- Small feature: start at `braindump2prd`; if the idea is still fuzzy, run `brainstorming` first.
- Feature already discussed in the chat: `braindump2prd` harvests the conversation instead of re-interviewing.
- PRD already written: `braindump2prd` in "Harvest PRD" mode adds only the spec.
- No tracker connected: everything works with files (`prd.md`, `spec.md`, `issues.md`); plans go to `plans/<branch>/`.
- Large project: `prd2issues` cuts the first milestone fully and leaves placeholders; run it again in update mode per milestone.

### A new web app

1. `/fullstack-scaffold` asks a few questions: name, realtime service yes/no,
   who logs in (internal staff, external users or both), CI platform
   (GitHub, GitLab or both), hostname. It generates the repo with current
   dependency versions and proves it with the repo's own `task ci`.
2. `task dev:up` starts the stack in the background at http://localhost:8000;
   `task --list` shows everything else. The generated CLAUDE.md files tell
   every agent how to start, stop, test and deploy.
3. Single sign-on works with any OpenID Connect provider (Entra ID, Google
   Workspace, Keycloak, Okta …): register the app there and set `SSO_*` in the
   encrypted env file. Steps are in the generated `docs/operations.md`.
4. Features: issues from `prd2issues`, built by you or the `fullstack-engineer`
   agent under the `fullstack-engineering` guideline; pull requests per
   `engineering-standards`.
5. Release: tag `vX.Y.Z` → pin it for staging → `task deploy ENV=staging` →
   verify → same version to production. Each server runs one shared Traefik
   (`plugins/fullstack-engineering/skills/fullstack-engineering/assets/traefik-host/`).

Existing repos on another stack are not migrated: the guideline applies its
stack-independent rules and flags the deviations that matter.

### An agent system

Design and build with `agentic-engineering` (framework roles, state,
validation, evals); `prompt-engineering` for the prompts and their evaluation.
Where the agents need a web app around them (users, admin, streaming UI),
combine it with `fullstack-engineering`: agent workloads run in its FastAPI
service and stream to the browser.

### UI design

From screenshots or a brief: `uiux-image2design` extracts a design system and
builds it in Penpot or Figma (`uiux-design-penpot`, `uiux-design-figma`),
following `uiux-design-system`. In code, tokens and components follow
`uiux-design-tailwindv4` and `uiux-design-vue3`, which the fullstack frontend
uses too. `design-parity` checks the built UI against the design.

## Organisation profile

`engineering-standards` reads its PR size guide, length limits and tracker
conventions from `references/profile.md`, which ships with neutral defaults.
Replace that file to adapt the standards to your team. Tracker and roadmap
tools are named only as examples (Linear, GitHub issues, Notion); every skill
also works with files.

## Migrating from earlier versions

`ai-dev`, `branch`, `braindump2spec`, `spec2plan`, `fullstack-dev` and
`code-review` were retired; installed copies get no more updates. Uninstall
them and install the replacements by hand:

| Retired | Replacement |
|---|---|
| `ai-dev` | `agentic-engineering` |
| `branch` | `engineering-standards` (includes `/branch`) |
| `braindump2spec` | `braindump2prd` |
| `spec2plan` | `prd2issues` (+ `agent-team` for parallel execution) |
| `fullstack-dev` | `fullstack-engineering` |
| `code-review` | Anthropic's `code-review` (PR review with confidence scoring) or `pr-review-toolkit`, both from `claude-plugins-official`; built-in `/security-review` |

## Local development

```bash
claude plugin validate .                     # check marketplace + all plugins
claude plugin marketplace add ./             # register this checkout locally
claude --plugin-dir ./plugins/<plugin-name>  # try one plugin without installing
```

See [CLAUDE.md](CLAUDE.md) for the repository layout, the `SKILL.md` format,
versioning rules and commit message conventions.
