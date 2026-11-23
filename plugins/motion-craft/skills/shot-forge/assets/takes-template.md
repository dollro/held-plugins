# Take log: <project> · <cut>

<!-- motion/shots/takes.md. Append one row per generation, the moment it returns, accepted or not.
     Never edit an earlier row; a re-judged take gets a new row with the same take number and a note.
     No API keys, tokens or signed URLs in this file. -->

Provider: <connected MCP> · model: <model id> · pricing checked: <YYYY-MM-DD>, <source>
Budget (intake.md): <amount currency> · estimate approved by <user> on <YYYY-MM-DD>

## Budget estimate

Seconds per take = duration_s + 1 (trim margin). Price per <second | clip | credit> = <price>.

| Shot | Beat | Generated s | Max takes | 1 take | Typical (2) | Cap (max takes) |
|---|---|---|---|---|---|---|
| <S01> | <B02> | <6> | <3> | <cost> | <cost> | <cost> |
| Reference stills | – | – | – | <cost> | <cost> | <cost> |
| **Total** | | | | <low> | <typical> | <cap> |

Cap vs budget: <cap> of <budget> (<percent>). Stop and ask before a take that would pass the approved cap.

## Takes

Verdict: planned · accept · revise_prompt · change_approach (approach). Prompt: the text if short, else `sha256:<first 12>` of prompts/<shot>-t<take>.txt.

| Shot | Take | Provider | Model | Prompt | Params | Seed | Cost | Verdict | File |
|---|---|---|---|---|---|---|---|---|---|
| <S01> | <1> | <provider> | <model> | <sha256:...> | <16:9, 6 s, 1080p, ref: refs/x.png> | <seed or –> | <0.00 EUR> | <verdict> | <clips/S01-t1.mp4> |

## Spend

Spent so far: <sum of Cost> of the approved cap <cap>.
