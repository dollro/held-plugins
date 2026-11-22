# Motion spec

The storyboard shows stills; the spec says how one becomes the next. Without it every change falls back to the same fade, and the film feels like slides. Write `motion/<cut>/motion-spec.md` after the storyboard is approved and before anything animates.

## 1. Lengths first

A frame that is too short pushes everything on screen in its first second, then freezes. Fix lengths before choosing moves.

- **Read time** for a line nobody speaks: 0.5 s + 0.3 s per word (for longer lines, roughly 1 s plus 45 ms a character). A spoken line: its VO length + 0.3 s.
- The **last line** of the film holds ≥ 2 s; the end card's ask holds ≥ 3 s with the URL.
- The **star** frame gets about twice the median frame. A UI demo holds one framing while the UI acts.
- Something new every 2-4 s, but a landed line stays still.
- Sum the lengths and compare with the cut runtime (±15%). If long, trim holds and gaps, never the read windows or the one deliberate stop (usually the silence after the reveal). Report the revised total to the user first, then retime.

## 2. House settings (state once)

| Setting | Default |
|---|---|
| Line arrival | Land: per word group, blur 6 → 0 px and opacity 0 → 1 in 0.13-0.2 s, `expo.out`; groups 0.06-0.12 s apart; no slide |
| Line after landing | dead still until it leaves; never drifting, breathing or scaling |
| Line exit | Blur out: 0.12-0.25 s, `power3.in`; exits 40-50% shorter than entrances |
| Line position | one home position per film (`direction.md`); two lines never cross |
| Hero colour | one element per frame |
| Footage | Push 1.00 → 1.04 over the shot, `power1.inOut`, or locked; never on UI |
| UI | real speed; dead time cut, never visibly sped up; crops at 1.6-2× real size; UI text ≥ 26 px at 1080p |
| Overlap | each element begins once its predecessor is 30-50% through |
| Springs | damping 0.7-0.85 (premium); position and scale only, never opacity or colour |
| Blur | motion blur on fast moves only, peaking mid-move; clear before hand-off |

## 3. Eases by job

| Job | Ease |
|---|---|
| arrival (lines, objects) | `expo.out` or `power4.out`: long tail, lands slow |
| camera move, colour flood | `power2.inOut` |
| exit, zoom through | `power3.in`: accelerates away |
| footage push | `power1.inOut` |
| a number counting | `expo.out`, ≤ 0.9 s |
| constant progress, rotation | linear, only when constant speed is the point |

Never the same 0.5 s `power2.out` on everything: that is the default that looks generated.

## 4. Named moves

Name every change with one of these, or define a new one in the spec's house settings.

| Move | What happens | Typical length |
|---|---|---|
| Land | a line or word group arrives (blur + opacity), then holds still | 0.13-0.2 s |
| Build | a line arrives word by word, one steady cadence for the film | 0.06-0.12 s per word |
| Count | a number rolls up to its value, then lands | ≤ 0.9 s |
| Blur out | a line or object leaves with blur and fade | 0.12-0.25 s |
| Hold | nothing moves; the deliberate stop | as read time needs |
| Push | slow scale on footage | the shot |
| Punch-in | cut or quick move to a closer framing inside a frame | 0.3-0.5 s |
| Settle | the arriving picture starts at 1.03 and settles to 1.0 | 0.3 s |
| Fold | many small things collapse, row by row, into one | 1-2 s |
| UI acts | the real recording plays; the camera holds | as the UI needs |
| Mark lands | the logo is carried in by an element on screen and settles | 0.6-1.0 s |

## 5. Seams (between frames)

Limit a film to 3-5 seam types, and let something visible trigger each one. At most a third of seams are hard cuts; worlds never crossfade into each other.

| Seam | How it is built |
|---|---|
| Collapse into / Grow through | an object shrinks into a glyph of the next frame, or grows past the frame edge and becomes its ground (0.5-0.7 s, `power2.inOut`) |
| Carry | an element shrinks (1 → 0.6, blur peak 6 px) and lands inside the next frame as it builds around it |
| Zoom through | the camera tracks to a target, which scales through the frame (0.35 s, `power3.in`); its fill becomes the next ground |
| Colour flood | the hero element stays; the whole ground changes colour (0.4 s, `power2.inOut`) |
| Word swap | shared words stay put; the others leave and new ones arrive in place (0.3-0.7 s) |
| Match cut | one shape or motion continues across a hard cut (a door, a circle, a tap) |
| Morph | one container widens into the next (a button into a panel) |
| Whip | a 0.13-0.3 s smear; the arriving element lands blurred and sharpens |
| Cut | a hard cut, on the fastest frame of a move or on a beat of the music |

## 6. Spec format

```markdown
# Motion spec · <product> · <cut>

## Lengths
| Frame | Beat | Start | Length | Longest read | Read time needed | OK |

## House settings
- <only what differs from or adds to section 2>

## Per frame
### Frame N · Bxx · <start>-<end> s
| t (s) | Element | Move | Length | Ease | Carries over |

## Seams
| Between | Kind | Cause on screen |

## Conflicts resolved
- <where the storyboard went against these rules, and what changed>
```

Every change in every frame has a row: element, named move, length, ease. Every seam has a kind and a cause. `t` is seconds into the film, so the spec lines up with the storyboard's `start` and with motion-qa's beat export.

## 7. What the user can say

| They say | Change |
|---|---|
| "too fast" | slow every camera move and zoom to 0.7× its speed; nothing else |
| "speed it up" | shorten holds and gaps; later frames move up; read windows stay |
| "the titles move" | let each line arrive, then freeze it until it exits |
| "it feels like slides" | pass into the next frame via something already visible; cut while a move is still running |
| "too busy" | one hero move per frame; secondary moves travel half as far, start 0.1-0.2 s later |
