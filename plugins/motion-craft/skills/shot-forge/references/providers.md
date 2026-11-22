# Providers: whichever generation MCP is connected

shot-forge never calls a provider's API itself and never stores a key. It uses the video-generation MCP server the user has connected to Claude Code. Dedicated video-generation services and hosted aggregators that front several video models both offer such servers; the skill works with any server that can turn a prompt (and optionally images) into a clip.

## 1. Find it

1. Look at the tools available in this session for names or descriptions with video generation in them (generate video, image to video, text to video, create clip). Load deferred tools if the session lists them by name only.
2. More than one: ask which to use, and say what each offers (section 2).
3. None: **stop**. Deliver shots.json, the character and continuity sheets and the budget estimate (priced with a labelled placeholder rate), and tell the user: no video-generation MCP is connected; connect one and run shot-forge again, or let motion-director replace the generated frames with motion or stills. Never fake a clip, never render a placeholder and call it a take.

## 2. Check its capabilities

Read them from the tool schemas and the provider's own model-info or pricing tool if it has one; ask the user for what the tools do not say. Record the answers in the takes.md header.

| Capability | Why it matters | If missing |
|---|---|---|
| Models offered | quality, speed and price differ per model | pick one model per film; switching mid-film breaks the look |
| Reference image (subject / character) | holds the face across shots | anchor text only; keep shots short; expect more takes |
| First frame (image to video) | start from an approved still | text to video; continuity rests on the prompt |
| Last frame | ends on a planned frame, joins a designed scene | cut on movement instead |
| Max duration per clip | shots over the limit are split | split in shots.json before pricing |
| Aspect ratios | the cut's aspect (16:9, 9:16, 1:1) | generate wider and crop; check the crop keeps the subject |
| Resolution | 1080p for a film, lower for drafts | draft low, final at 1080p, only for accepted prompts |
| Audio | most generated audio is unusable for a film | turn it off; sound comes from the build |
| Seed | repeat a take with one change | log "–"; a repeat is a new lottery |
| Negative prompt | where "text, logo, screen" may go | leave it out; rely on the positive prompt and the critic |
| Price | per second of output, per clip, or credits | ask; convert credits to the intake currency and say how |
| Async jobs | some return a job id to poll | poll with the provider's status tool; log the take only when the file exists |

## 3. Price it

- Price = seconds generated (duration_s + 1 per take) × price per second, or clips × price per clip. Per second of **output**, not of compute.
- State the date and source of the price. Prices change monthly; an estimate older than 30 days is re-checked before generating.
- Convert to the currency of the intake budget; give the rate used.
- Show three figures: one take per shot, typical (two), cap (`max_takes`). Compare the cap with the intake budget.

## 4. Keys and files

- Keys live in the MCP server's own configuration or environment, never in shots.json, takes.md, prompts or the repo. If a tool asks for a key as an argument, stop and ask the user to configure the server instead.
- Signed or expiring download URLs are not logged. Download the clip to `motion/shots/clips/<shot>-t<take>.<ext>` and log that path.
- Check the provider's terms for commercial use of generated clips before the film ships; note the answer in takes.md.
