# story-craft

The story before any slide or frame. story-craft settles what a launch, keynote or product film must achieve and what it can stand on, before any medium is chosen. Its files are read by deck-craft (keynote decks) and motion-craft (films).

## Modules

| Skill | Job | Output |
|---|---|---|
| `stock-take` | Interview + inventory: purpose (belief before → after), ask, audience, outputs with channel and runtime, evidence tagged solid / likely / missing, assets, constraints | `intake.md` |

Planned: `narrative` (medium-neutral dramaturgy, numbered beats and cuts → `narrative.md`) and `story-review` (review gate with validator).

In Claude Code the skill is invoked as `/story-craft:stock-take` or picked up from the request.

## Decisions

- **Separate plugin.** story-craft, deck-craft and motion-craft are three plugins. deck-craft keeps working without story-craft installed and in the PowerPoint add-in.
- **One language per narrative.** A story is written in one language; another language is a separate cut or a translated file.
- **Evidence is tagged, never upgraded.** `missing` evidence cannot carry a claim downstream.

## Install (Claude Code)

```bash
claude plugin install story-craft@held-plugins
```

## Sources and credits

- Interview pattern (one question at a time, sources before questions, import of a PR/FAQ) adapted from prfaq-vision-builder in this marketplace and Amazon's Working Backwards method.
- Nancy Duarte, Resonate (audience belief before and after).

License: MIT (see `LICENSE`).
