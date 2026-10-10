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
|`prd2issues`|1.1.0|Cut a Ready PRD into a few readable, codebase-grounded tracker issues|

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
