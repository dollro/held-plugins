---
name: design-first
description: "Turns a feature idea or behaviour change into an agreed design through short dialogue: explores the project, asks one question at a time, proposes 2-3 approaches, gets approval before any code. Use before building a new feature, component or behaviour change whose approach is still open, or when someone says \"let's design this\", \"think this through first\", \"how should we build X\". Skip for changes whose diff fits in one sentence. Not for writing a PRD (braindump2prd)."
---

# Design first

Turn an idea into an agreed design through collaborative dialogue, then hand off to the right tool for building it.

Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you're building, present the design and get the user's approval before any implementation.

## When to use it, when to skip it

Design before code when the approach is uncertain, the change touches several files or components, or the code is unfamiliar. Unexamined assumptions in "simple" features waste the most work, so when in doubt, write a short design (a few sentences) and get a yes.

**Skip it** when the change is small and its scope is clear: you could describe the diff in one sentence, or it is a single obvious edit (a typo, a log line, a rename, a config value). Say so in one line and do it directly.

Until the design is approved: no code, no scaffolding, no implementation skills.

Inside an autonomous run (a `/goal`, `claude -p`, a sandbox launched for a task) don't interview: pick the approach that fits the spec's constraints, record it and the open questions in the final report.

## Checklist

Create a task for each item and complete them in order:

1. **Explore project context:** files, `docs/`, CLAUDE.md, recent commits, the tracker issue if there is one.
2. **Ask clarifying questions:** one at a time; purpose, constraints, success criteria.
3. **Propose 2-3 approaches** with trade-offs and your recommendation.
4. **Present the design** in sections scaled to their complexity; get approval after each section.
5. **Record the outcome** where it lasts (After the design, below).
6. **Hand off** to the right next step (Hand-off, below).

## The process

**Understanding the idea:**
- Check the current project state first (files, docs, recent commits).
- Ask questions one at a time; prefer multiple choice, open-ended is fine too.
- One question per message; if a topic needs more, break it into several questions.
- Focus on purpose, constraints and success criteria, including how the result will be checked (a test, a command, a screenshot).

**Exploring approaches:**
- Propose 2-3 approaches with trade-offs.
- Lead with your recommendation and explain why.

**Presenting the design:**
- Scale each section to its complexity: a few sentences if straightforward, up to 200-300 words if nuanced.
- Ask after each section whether it looks right so far.
- Cover: architecture, components, data flow, error handling, testing and the end-to-end check that proves it works.
- Go back and clarify when something doesn't make sense.

## After the design

The design is not a durable file in the repo. Follow the engineering-standards split if installed:

- **Decisions and the agreed design** go where the team sees them: on the tracker issue, or into the PRD/spec (braindump2prd) when the work becomes a project. Without a tracker, they go into the pull request description.
- **Scratch notes** may go to `./plans/<branch-name>/` (branch `/` becomes `-`, e.g. `feat/meeting-copilot` → `./plans/feat-meeting-copilot/`). That folder is disposable: do not commit it as a record, and do not rely on it surviving.
- **Lasting architecture** goes into `docs/` with the pull request that implements it, describing the code as it then is.

## Hand-off

Pick the next step by the size of the work and say which one and why:

| Work | Next step |
|-|-|
| Fits one reviewable pull request | Plan mode (`Shift+Tab` or `claude --permission-mode plan`) for the implementation plan, then build. With engineering-standards: `/branch <type>/<name>`, then its "Implement an issue" flow |
| Several issues or a feature with open product questions | `braindump2prd` (harvest mode: turns this conversation into PRD and spec), then `prd2issues` to cut it into one-PR issues |
| 3+ independent parts to build in parallel | `agent-team`, after the issues or plan exist |

For a large implementation, start it in a fresh session with the agreed design as the prompt or on the issue, so the build runs on clean context. Before any unattended run, the human chooses where it runs (engineering-standards `references/autonomous-runs.md`).

## Key principles

- **One question at a time.** Don't overwhelm with multiple questions.
- **Multiple choice preferred.** Easier to answer than open-ended.
- **YAGNI.** Remove unnecessary features from every design.
- **Explore alternatives.** Propose 2-3 approaches before settling.
- **Incremental validation.** Present the design, get approval before moving on.
- **Proportionate.** The design is as long as the change needs, and no design at all for a one-sentence change.
