# atlas: the whole chain

A worked example for the dummy product **atlas** (fictional company Acme, sample data): one story, a keynote deck and a 60-second film, sharing beat IDs. Run it from the repository root. Each step names the skill an agent would use and the command that checks its output.

Requirements: Python 3.9+ with `pyyaml` and `python-pptx>=1.0,<1.1` (Pillow optional), ffmpeg and ffprobe; LibreOffice and poppler only for slide renders.

```bash
pip install pyyaml "python-pptx>=1.0,<1.1" pillow
R=$(pwd); SC=$R/plugins/story-craft; DC=$R/plugins/deck-craft/skills; MC=$R/plugins/motion-craft
```

| # | Skill | Input → output | Here |
|-|-|-|-|
| 1 | story-craft:stock-take | interview, sources → `intake.md` | `intake.md` (7 evidence rows, one `missing`) |
| 2 | story-craft:narrative | `intake.md` → `narrative.md` | 17 beats, cuts keynote / film-60 / teaser-20 |
| 3 | story-craft:story-review | → `## Review` | PASS after seven beat fixes by a fresh reviewer |
| 4 | deck-craft:deck-design-guide | master → `design-guide.json` → `brand-lock.md` | fictional Acme master |
| 5 | deck-craft:deck-keynote | `narrative.md` → `storyboard.md` | `storyboard.md` (Beat column = cut keynote) |
| 6 | motion-craft:motion-director | `narrative.md` + `brand-lock.md` → `film-60/STORYBOARD.md` | `motion-craft/examples/atlas/film-60/` (dry run, nine frames) |
| 7 | motion-craft:shot-forge | frames with `medium: generated` → `shots.json` | `motion-craft/examples/atlas/shots/` (no clips generated) |
| 8 | motion-craft:motion-qa | render → `renders/beats/*`, `clips.json` | test-fixture film stands in for the HyperFrames render |
| 9 | deck-craft | `clips.json` → video slides | B02 and B12 play their clips |

```bash
# 1-3 story: contract and review gate
python $SC/scripts/validate_narrative.py $SC/examples/atlas/narrative.md          # PASS, exit 0
python $SC/scripts/test_validate_narrative.py -v                                    # 4 tests OK, one asserts a mutated copy fails with exactly 3 findings

# 4 brand: fictional master → design guide → brand lock
python $DC/deck-design-guide/examples/make_acme_master.py /tmp/acme-master.pptx
python $DC/deck-design-guide/scripts/template_profile.py /tmp/acme-master.pptx /tmp/acme
python $DC/deck-design-guide/scripts/export_brand_lock.py /tmp/acme/design-guide.json --template /tmp/acme-master.pptx
#   expected: "MISSING font files: Inter" (the fictional brand ships no font files). In a real project,
#   copy brand-lock.md and logos/ into the motion project; the example already has its copy in $MC/examples/atlas/

# 5 keynote storyboard from the narrative
python $DC/deck-keynote/scripts/storyboard_from_narrative.py --check $SC/examples/atlas/storyboard.md $SC/examples/atlas/narrative.md

# 6-7 film plan and generated-shot specs
python $MC/skills/motion-director/scripts/check_storyboard.py $MC/examples/atlas/film-60/STORYBOARD.md
python $MC/scripts/validate_shots.py $MC/examples/atlas/shots/shots.json --storyboard $MC/examples/atlas/film-60/STORYBOARD.md

# 8 render (test fixture here; HyperFrames in a real project), checks, beat export
python $MC/skills/motion-qa/scripts/make_test_film.py $MC/examples/atlas --cut film-60 --size 1920x1080
python $MC/skills/motion-qa/scripts/render_checks.py $MC/examples/atlas/renders/film-60.mp4 --storyboard $MC/examples/atlas/film-60/STORYBOARD.md
python $MC/skills/motion-qa/scripts/export_beats.py $MC/examples/atlas --cut film-60

# 9 the deck plays the film's B02 and B12 clips (built in a scratch folder)
cd "$(mktemp -d)"
python $DC/deck-craft/examples/atlas_keynote.py $MC/examples/atlas/renders/clips.json
python $DC/deck-craft/scripts/check_deck.py atlas_keynote.pptx                     # 0 errors; 1 warning: the B06 product-shot placeholder
python $DC/deck-craft/scripts/render.py atlas_keynote.pptx                         # contact sheet marks VIDEO B02, B12
```

What the example does not do: run HyperFrames (motion-director stops at the storyboard and motion spec without it), generate footage (shot-forge needs a connected video MCP and a budget approval), or play the clips in PowerPoint (open the deck and click each video once).
