# held-plugins

A curated marketplace of [Claude Code](https://claude.ai/code) plugins — skills and
agents for AI agent development, spec-driven workflows, product management, full-stack and desktop
development, UI/UX design systems, and financial analysis.

Maintained by Held.

## Install

```
/plugin marketplace add dollro/held-plugins
```

Then run `/plugin` to browse and enable what you want. Enabled plugins are
referenced as `<plugin-name>@held-plugins`.

## Idea to merged PR: the workflow

The product, workflow and development plugins are built to chain. Each step
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
                  │   domain skills while building: agentic-engineering,
                  │   fullstack-dev, electron-dev, uiux-*, prompt-engineering
                  └───────────┬───────────┘
                     code-review (+ design-parity for UI)
                              │
                     merge, one PR at a time
```

|#|step|plugin|output|
|-|-|-|-|
|1|Vision (new products, optional)|`prfaq-vision-builder`|One PR/FAQ document: future press release plus lean FAQ|
|2|Order the work|`product-roadmap-3-layers`|Now/Next/Later roadmap: outcomes → features → tech enablers|
|3|Specify one feature|`braindump2prd`|`braindump_final.md` (interview record) → `prd.md` + `spec.md`, handed to the tracker project|
|4|Cut into issues — run in the product repo|`prd2issues`|1–3 issues per result, each one reviewable PR, with files, pattern to follow, check command, `Blocked by` and `Parallel`|
|5a|Build one issue|`engineering-standards`|`/branch` → short plan on the issue → code → checks, cheapest first → `docs/` update → PR|
|5b|Build several issues at once|`agent-team`|Independent issues: one agent each in its own worktree. "Sync before merge" pairs: shared contract first|
|6|Review|`code-review`, `design-parity`|Findings on the PR; design-vs-implementation diff for UI|

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

**Organisation profile.** `engineering-standards` reads its PR size guide,
length limits and tracker conventions from `references/profile.md`, which ships
with neutral defaults. Replace that file to adapt the standards to your team.

**Migrating from earlier versions.** `ai-dev`, `branch`, `braindump2spec` and
`spec2plan` were retired. Replace them with `agentic-engineering`,
`engineering-standards`, `braindump2prd` and `prd2issues` (+ `agent-team` for
parallel execution).

## What's inside

### AI agent development

|plugin|version|what it does|
|-|-|-|
|`agentic-engineering`|2.0.0|Standards and guardrails for production agentic AI on LangGraph, Pydantic AI, CrewAI, and Langfuse|
|`prompt-engineering`|2.0.1|Prompt design, evaluation frameworks, and production prompt systems|

### Workflows

|plugin|version|what it does|
|-|-|-|
|`agent-team`|2.0.0|Run parallel agents (teams, worktrees) with contracts, parallel-safety and quality gates|
|`brainstorming`|1.0.0|Structured exploration of intent and design before implementation|
|`code-review`|2.0.0|Review for completeness, security, performance, and best practices|
|`engineering-standards`|1.1.0|Small reviewable PRs, CLAUDE.md and docs structure, `/branch`; swappable org profile|

### Product management

|plugin|version|what it does|
|-|-|-|
|`prfaq-vision-builder`|1.0.1|Working Backwards PR/FAQ vision document|
|`product-roadmap-3-layers`|1.0.1|3-layer Now/Next/Later product roadmap, from an interview or a Notion database|
|`braindump2prd`|1.1.3|Interview a PM and write a plain-language PRD and spec for the issue tracker|
|`prd2issues`|1.1.1|Cut a Ready PRD into a few readable, codebase-grounded tracker issues|

### Development

|plugin|version|what it does|
|-|-|-|
|`electron-dev`|2.0.1|Secure cross-platform desktop apps with Electron|
|`fullstack-dev`|2.0.1|End-to-end feature delivery from database to UI|
|`design-parity`|2.0.0|Close the gap between a Claude Design spec and its implementation|
|`uiux-design-system`|4.0.0|Design system architecture, token hierarchy, and naming conventions|
|`uiux-design-figma`|1.1.0|UI/UX design in Figma via figma-console-mcp|
|`uiux-design-penpot`|2.7.0|UI/UX design in Penpot via MCP tools|
|`uiux-design-tailwindv4`|1.0.0|Tailwind CSS v4 design systems with CSS-first configuration|
|`uiux-design-vue3`|1.0.0|Vue 3 with Composition API, Pinia, Router, and testing|
|`uiux-image2design`|3.0.1|Extract a design system from screenshots into Penpot or Figma|
|`pencil-pen-generator`|1.0.0|Generate and convert Pencil `.pen` design files|

### Analysis

|plugin|version|what it does|
|-|-|-|
|`equity-research`|1.0.0|Equity research with chance/risk reports and DCF valuation|
|`investment-memo`|1.0.0|VC investment memos from pitch decks and DD materials|

## Contributing

See [CLAUDE.md](CLAUDE.md) for the repository layout, the `SKILL.md` format,
versioning rules, and commit message conventions.
