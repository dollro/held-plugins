# story-craft

The story before any slide or frame. story-craft settles what a launch, keynote or product film must achieve and what it can stand on, before any medium is chosen. Its files are read by deck-craft (keynote decks) and motion-craft (films).

## Modules

| Skill | Job | Output |
|---|---|---|
| `stock-take` | Interview + inventory: purpose (belief before → after), ask, audience, outputs with channel and runtime, evidence tagged solid / likely / missing, assets, constraints | `intake.md` |
| `narrative` | Medium-neutral dramaturgy: headline, villain, cost, promise, three storylines then one, sparkline, reveal, rule of three, proof per claim, STAR moment, close; numbered beats `B01..Bn` with roles and evidence IDs; cuts per output | `narrative.md` |

Planned: `story-review` (review gate with validator).

An end-to-end example for the dummy product `atlas` is in `examples/atlas/`.

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
- Nancy Duarte, Resonate (audience belief before and after, the sparkline of what is and what could be, the STAR moment).
- Carmine Gallo's analyses of product-launch keynotes (headline, villain and hero, rule of three, meaningful numbers); the launch dramaturgy was moved here from deck-craft:deck-keynote.
- "Three storylines, then one", hook rules and the tells of a generic film adapted from the story reference of HyperFrames (heygen-com/hyperframes, Apache-2.0).
- Cutdown rules ("drop beats from the middle, never the hook or the payoff") adapted from video-director (SallyRS/video-director, MIT).

License: MIT (see `LICENSE`).
