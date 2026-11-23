# Motion spec · atlas · film-60

Illustrative example · Fictional company (Acme) and sample data.
Storyboard: `STORYBOARD.md` (9 frames, 60.0 s) · Direction: "The pile" (`direction.md`) · Moves named as in motion-director `references/motion-spec.md`.

## Lengths

| Frame | Beat | Start | Length | Longest read | Read time needed | OK |
|---|---|---|---|---|---|---|
| 1 | B02 | 0.0 | 7.0 | "47 photos. 3 voice memos. Zero report." (6 words) | 2.3 s | yes |
| 2 | B03 | 7.0 | 6.0 | number + "hours a week" + fine print | 3.4 s | yes |
| 3 | B05 | 13.0 | 5.0 | the question (9 words) | 3.2 s | yes |
| 4 | B06 | 18.0 | 4.0 | "atlas" + silence | 0.8 s + 2.6 s stop | yes |
| 5 | B09 | 22.0 | 5.0 | "Report in one tap." | 1.7 s | yes |
| 6 | B12 | 27.0 | 14.0 | four UI steps + "Report done." | 12.0 s of UI acting | yes |
| 7 | B15 | 41.0 | 6.0 | quote (8 words) + attribution | 3.4 s | yes |
| 8 | B16 | 47.0 | 6.0 | "Home on time on Friday." | 2.0 s | yes |
| 9 | B17 | 53.0 | 7.0 | ask + URL | 3.0 s hold | yes |

Total 60.0 s against 60 s runtime. The star (B12) gets about twice the median frame.

## House settings

- **Lines**: Land (per word group: blur 6 → 0 px, opacity 0 → 1, 0.15 s `expo.out`, groups 0.08 s apart). Landed lines are dead still. Exit: Blur out, 0.12 s `power3.in`.
- **Line home**: upper band, top of cap height at 9% of frame height, left aligned to the brand-lock safe margin (3.8% of frame width). Statement size 6% of frame height; one hero word in `colors.hero`.
- **Hero colour**: once per frame, on the word or number that matters (Zero, 6.5, atlas, done, the mark). Never on grounds, never on two things at once.
- **Footage**: Push 1.00 → 1.04 over the shot, `power1.inOut`; no push on UI.
- **UI**: the recording plays at 1.0× except dead time, cut out (never sped up visibly); crops at 1.6-2× real size; text ≥ 26 px at 1080p.
- **Springs**: only on the end-card mark, damping 0.8; never on opacity or colour.
- **Seams**: 8 between frames, 5 kinds, 1 hard cut (the match cut 7 → 8).

## Per frame

### Frame 1 · B02 · 0.0-7.0 s

| t (s) | Element | Move | Length | Ease | Carries over |
|---|---|---|---|---|---|
| 0.0 | footage S01 (car, phone) | Push | 7.0 | `power1.inOut` | the car returns in frame 7 |
| 0.0 | phone screen grid | Fill (rows add, 3 per second) | 6.0 | `steps` per row | the grid becomes frame 2's "6" |
| 1.2 | "47 photos." | Land | 0.15 | `expo.out` | – |
| 2.6 | "3 voice memos." | Land | 0.15 | `expo.out` | – |
| 4.2 | "Zero report." ("Zero" hero) | Land, after a 0.4 s Hold | 0.15 | `expo.out` | – |
| 6.6 | all three lines | Blur out | 0.12 | `power3.in` | – |

### Frame 2 · B03 · 7.0-13.0 s

| t | Element | Move | Length | Ease | Carries over |
|---|---|---|---|---|---|
| 7.0 | phone grid → "6.5" | Carry (the grid shrinks into the glyph "6", footage blurs 15 px and fades) | 0.6 | `power2.inOut` | – |
| 7.2 | "6.5" | Count (0.0 → 6.5) | 0.8 | `expo.out` | – |
| 8.4 | "hours a week" | Land | 0.15 | `expo.out` | – |
| 10.2 | fine print "Median, survey of 120 site managers." | Fade 0.3, then hold | 0.3 | `power2.out` | – |
| 12.8 | everything but "6.5" | Blur out | 0.12 | `power3.in` | "6.5" stays for the flood |

### Frame 3 · B05 · 13.0-18.0 s

| t | Element | Move | Length | Ease | Carries over |
|---|---|---|---|---|---|
| 13.0 | ground dark → light | Colour flood | 0.4 | `power2.inOut` | – |
| 13.0 | "6.5" | Blur out | 0.15 | `power3.in` | – |
| 13.2 | question, word by word | Build (0.1 s apart) | 1.0 | `expo.out` per word | "before" stays for frame 4 |
| 15.4-17.6 | question | Hold | 2.2 | – | – |

### Frame 4 · B06 · 18.0-22.0 s

| t | Element | Move | Length | Ease | Carries over |
|---|---|---|---|---|---|
| 18.0 | all words but "before" | Word swap (out) | 0.3 | `power2.in` | – |
| 18.3 | "before" → "atlas" set in the heading font (hero) | Word swap (in, same position) | 0.4 | `expo.out` | – |
| 18.7-21.6 | "atlas" | Hold (the silence) | 2.9 | – | – |
| 21.6 | "atlas" | Lift and shrink to 0.4 while tiles arrive | 0.4 | `power3.in` | – |

### Frame 5 · B09 · 22.0-27.0 s

| t | Element | Move | Length | Ease | Carries over |
|---|---|---|---|---|---|
| 22.0 | photo tiles from frame 1 | Carry (enter from left edge, blur peak 6 px) | 0.6 | `power3.out` | same tiles as frame 1 |
| 23.2 | tiles → report page | Fold (row by row, 0.12 s apart) | 1.6 | `power2.inOut` | the page is the zoom target |
| 24.6 | "Report in one tap." ("one tap" hero) | Land | 0.15 | `expo.out` | – |
| 26.6 | line | Blur out | 0.12 | `power3.in` | – |

### Frame 6 · B12 · 27.0-41.0 s

| t | Element | Move | Length | Ease | Carries over |
|---|---|---|---|---|---|
| 27.0 | report page → phone | Zoom through (page scales 1 → 2.5, its white becomes the app's ground) | 0.35 | `power3.in` | – |
| 27.35 | UI recording | Settle (comes in at 1.03, settles to 1.0) | 0.3 | `expo.out` | – |
| 27.5 | three photos added | UI acts (real recording) | 3.0 | – | – |
| 27.5 | "Three photos." | Land, upper band | 0.15 | `expo.out` | – |
| 30.5 | memo recorded | Punch-in on the record control (1.6×) | 0.4 | `power2.inOut` | – |
| 30.6 | "One memo." | Land (replaces previous line in place) | 0.15 | `expo.out` | – |
| 33.0 | tap → report fills | Pull back to whole screen, then UI acts | 0.5 | `power2.inOut` | – |
| 36.0 | check + send | UI acts; punch-in on Send | 0.4 | `power2.inOut` | the send arrow returns on the end card |
| 39.0 | "Report done." ("done" hero) | Hold 0.4 s, then Land | 0.15 | `expo.out` | – |
| 40.6 | sent report | Carry (shrinks 1 → 0.6, blur peak 6 px, towards frame 7's windscreen) | 0.4 | `power3.in` | – |

### Frame 7 · B15 · 41.0-47.0 s

| t | Element | Move | Length | Ease | Carries over |
|---|---|---|---|---|---|
| 41.0 | footage (car park, dusk) | Push | 6.0 | `power1.inOut` | – |
| 41.0 | sent report | Carry lands in the windscreen reflection, fades 0.3 | 0.3 | `power3.out` | – |
| 41.3 | quote | Build (word groups 0.1 s apart) | 0.8 | `expo.out` | – |
| 44.0 | "Site manager, atlas pilot" | Fade | 0.3 | `power2.out` | – |
| 46.6 | car door closes | Match cut (on the closing door) | cut | – | door motion continues in frame 8 |

### Frame 8 · B16 · 47.0-53.0 s

| t | Element | Move | Length | Ease | Carries over |
|---|---|---|---|---|---|
| 47.0 | footage S02 (front door) | Push | 6.0 | `power1.inOut` | – |
| 49.0 | "Home on time on Friday." ("Friday" hero) | Land | 0.15 | `expo.out` | – |
| 52.6 | line | Blur out | 0.12 | `power3.in` | – |

### Frame 9 · B17 · 53.0-60.0 s

| t | Element | Move | Length | Ease | Carries over |
|---|---|---|---|---|---|
| 53.0 | footage → light ground | Colour flood | 0.4 | `power2.inOut` | – |
| 53.2 | send arrow → brand mark (`logos/acme-logo.png`) with "atlas" beside it | Mark lands (arrow carried in, hands over to the logo file, spring damping 0.8) | 0.9 | spring 0.8 | – |
| 54.4 | "Free pilot. One site. 30 days." | Land (three groups, 0.12 s apart) | 0.4 | `expo.out` | – |
| 56.6 | "atlas.example.com" | Land | 0.15 | `expo.out` | – |
| 57.0-60.0 | everything | Hold | 3.0 | – | – |

## Seams

| Between | Kind | Cause on screen |
|---|---|---|
| black → 1 | Cut | frame 0 is the pile (hook) |
| 1 → 2 | Carry | the grid shrinks into the number |
| 2 → 3 | Colour flood | the cost gives way to the question |
| 3 → 4 | Word swap | "before" becomes the name |
| 4 → 5 | Carry | the tiles of the pile return |
| 5 → 6 | Zoom through | the abstract page opens the real app |
| 6 → 7 | Carry | the sent report lands in the car |
| 7 → 8 | Match cut | the car door closes, the front door opens |
| 8 → 9 | Colour flood | evening light gives way to the brand ground |

## Conflicts resolved

- Storyboard draft had frame 4 at 3 s: too short for a name plus silence; now 4 s, taken from frame 9's hold (was 8 s).
- Frame 6 first drew the words over the UI; moved to the upper band so no UI text is covered.
- Frames 2 and 9 both entered with a fade; frame 2 now carries the grid into the number, frame 9 floods.
- Draft used 7 seam kinds; merged to 5 (Collapse into → Carry, Whip dropped).
