# Direction · atlas · film-60

Illustrative example · Fictional company (Acme) and sample data.
Narrative: `../../../../story-craft/examples/atlas/narrative.md` (Review: PASS) · Brand: `../brand-lock.md` · Style picked: Product close-up + Graded footage and type (`styles.md`).

## Options shown · beat B02 (frame 1, the hook)

Same beat, same statement ("47 photos. 3 voice memos. Zero report."), three different central ideas. Shown as stills: the start and end of frame 1, plus the first frame of frame 2 so the hand-off is visible.

### A · "The pile" (recommended)

- **Idea**: one phone holds the whole evening; the pile on it keeps growing until it becomes the number.
- **Start still**: dusk inside a car, rain on the windscreen, a phone propped on the steering wheel; its screen is a gallery grid of site photos (concrete, a cracked tile, a plan with pencil marks). Upper left: "47 photos." in heading type, ink on a light band.
- **End still**: the grid has filled the screen; the three lines stacked upper left; "Zero" in hero orange (#E8590C). Hands rest on the wheel, not touching the phone.
- **Lead medium**: generated footage (car, hands) with the screen composited as motion graphics.
- **Recurring element**: the photo tiles: the pile (B02) → folded into one page (B09) → three of them in the real demo (B12).
- **Moving between ideas**: carry and collapse (the thing on screen becomes the next frame).
- **End line**: "Free pilot. One site. 30 days."
- **Cost**: 2 generated shots (S01 car, S02 front door) + 1 car-park plate; the demo is a real recording.

### B · "Counter"

- **Idea**: type carries the argument; the numbers are the picture.
- **Start still**: flat dark ground (#2E3440), a single counter "47" in hero orange at 30% of frame height, "photos" small beside it.
- **End still**: three counters side by side (47 · 3 · 0), the "0" in orange, the others in ink-on-dark.
- **Lead medium**: motion graphics only; no footage.
- **Recurring element**: the counter digits, which roll to "6.5" in B03 and to "1 tap" in B09.
- **Moving between ideas**: slot-roll of the digits; colour floods between chapters.
- **End line**: same.
- **Cost**: cheapest; no generated shots. Risk: three numbers in a row read as a KPI grid and the evening (the feeling) is lost.

### C · "One defect"

- **Idea**: one crack in a wall travels through the whole film: photo → memo → report → the client's inbox.
- **Start still**: macro shot of a hairline crack in fresh plaster, a phone's shutter frame closing around it.
- **End still**: the crack's photo, small, one tile in a growing gallery; "47 photos." lands as the camera pulls back.
- **Lead medium**: generated macro footage + motion graphics.
- **Recurring element**: the crack.
- **Moving between ideas**: endless zoom (every frame dives into a detail that is the next frame).
- **End line**: same.
- **Cost**: most generated footage (5-6 shots with tight continuity on one crack). The narrative already rejected this storyline for budget ("Storylines considered", option 3).

## Pick

2026-11-22 · owner picked **A · "The pile"**. Reason (owner's words): "Every site manager has that phone in that car. B is clean but nobody feels it." Matches the narrative's chosen storyline (the evening pile) and the review note: keep B02 and B12 as a visual pair. From B: the slot-roll is kept for the "6.5" in frame 2.

## Look decisions

| # | Decision | Options shown | Pick | Values |
|---|---|---|---|---|
| 1 | How the product is shown | real UI recording · UI rebuilt from the recording · hands and phone, little UI | real UI recording | atlas test account, new report from 3 photos + 1 memo; crop 1.6-2×; placeholder until recorded |
| 2 | Colour treatment | light ground, hero rationed · dark ground throughout · ground changes per act | light ground, hero rationed | ground #F4F1EC (light_ground), ink #1B1B1F, hero #E8590C on one thing per frame, dark ground #2E3440 only in frame 2 (the cost) |
| 3 | Footage grade | documentary dusk · bright daylight · desaturated with hero-colour accents | documentary dusk | warm practicals, blue hour outside, no teal-orange push, 3% grain |
| 4 | Signature scene (B12) layout | phone centred on ground · phone right, words left · full-screen UI | phone right, words upper left | phone 70% of frame height, words in the upper band, never over the UI |
| 5 | Line placement | upper band · centred · lower third | upper band | cap height at 9%, left at the 3.8% safe margin; bottom 17% kept clear for the fine print and phone captions |
| 6 | Type | Inter only · Inter + body face for fine print | Inter for statements, Liberation Sans for fine print | font files **missing** in brand-lock (`font_files` empty): build holds until the files are supplied |

## Open

- Font files for Inter and Liberation Sans: needed before the animated test (no system fallback in renders).
- B12 recording: owner to record on the test account (steps listed in STORYBOARD.md frame 6).
- Generated shots S01, S02 and the car-park plate go to shot-forge after storyboard approval and a budget OK.
