# Take log: atlas · film-60

Illustrative example · Fictional company (Acme). No clip has been generated: the row below is a planned take, prices are illustrative.

Provider: <connected video-generation MCP> · model: <model id> · pricing checked: <YYYY-MM-DD>, provider pricing tool
Budget (intake.md): 600 EUR for generated footage · estimate approved by <owner> on <YYYY-MM-DD>

## Budget estimate

Seconds per take = duration_s + 1 (trim margin). Price: 0.40 EUR per second of output (illustrative; replace with the connected provider's price on the day).

| Shot | Beat | Generated s | Max takes | 1 take | Typical (2) | Cap (3) |
|---|---|---|---|---|---|---|
| S01 | B02 | 6 | 3 | 2.40 | 4.80 | 7.20 |
| S02 | B02 | 4 | 3 | 1.60 | 3.20 | 4.80 |
| S03 | B15 | 5 | 3 | 2.00 | 4.00 | 6.00 |
| S04 | B16 | 7 | 3 | 2.80 | 5.60 | 8.40 |
| Reference stills (2, plus retries) | – | – | – | 1.00 | 1.00 | 1.00 |
| **Total** | | 22 | | **9.80 EUR** | **18.60 EUR** | **27.40 EUR** |

Cap vs budget: 27.40 of 600 EUR (about 5 %). Even at five times the illustrative price the cap stays under a quarter of the budget, so no shot needs to be cut for money; the take cap of 3 per shot holds anyway.

## Takes

Verdict: planned · accept · revise_prompt · change_approach (approach). Prompt: the text if short, else `sha256:<first 12>` of prompts/<shot>-t<take>.txt.

| Shot | Take | Provider | Model | Prompt | Params | Seed | Cost | Verdict | File |
|---|---|---|---|---|---|---|---|---|---|
| S01 | 1 | <provider> | <model> | prompts/S01-t1.txt (from shots.json S01) | 16:9, 6 s, 1080p, ref: characters/refs/site-manager-front.png | – | 2.40 EUR (est.) | planned | – |

## Spend

Spent so far: 0.00 EUR of the approved cap 27.40 EUR.
