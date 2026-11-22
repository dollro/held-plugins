# Intake · atlas

Illustrative example · Fictional company (Acme) and sample data.

Purpose: site reports are an evening chore that comes after the real work → site reports can be finished on site, before you leave
Ask: start a free 30-day pilot on one site
Audience: site managers on mid-size builds; their week is three to five site visits, phone calls in between, and Friday evenings spent turning photos and voice memos into reports; they call it "the paperwork after the work" (from interviews.md)
Decision maker vs user: user is the site manager; the decision is made by the head of operations, who cares about disputed defects and same-day records
Source docs: prfaq.md: yes · PRD: no · interviews: yes (interviews.md, 9 site managers) · survey: yes (survey n=120) · analytics: yes (pilot export) · existing deck: no

## Outputs

| ID | Channel | Runtime | Speaker | Notes |
|---|---|---|---|---|
| keynote | live stage, trade fair | 15 min | yes | live demo possible on the stage laptop |
| film-60 | landing page | 60 s | no | sound on, VO in English |
| teaser-20 | social feeds | 20 s | no | muted autoplay, text carries the claim |

## Evidence inventory

| ID | Claim it could support | Evidence | Source | Strength |
|---|---|---|---|---|
| E1 | reports take too long | 6.5 h per week median spent on site reports | survey of site managers, n=120, Acme, spring | solid |
| E2 | the evening pile is the pain | three quotes describing "photos, memos, no report" at the end of the day | interviews.md, 3 of 9 site managers | likely |
| E3 | 40% faster than the leading competitor | owner is sure, nothing measured | – | missing |
| E4 | reports go out the same day | 91% of reports sent same day vs 23% before | pilot export, 14 site managers, 6 weeks | likely |
| E5 | far less time on reports | weekly report time 6.2 h → 1.4 h | pilot export, same pilot, self-reported baseline | likely |
| E6 | works without signal | 72 h offline, 0 lost entries, sync on reconnect | internal test protocol T-12, 3 devices | solid |
| E7 | site managers like it | "I sent the report from the car park. First time in ten years." | pilot user, site manager at a mid-size builder, agreed to be quoted by role | solid |

## Asset inventory

Brand: design-guide.json: yes (from deck-craft:deck-design-guide, acme-master.pptx) · master .pptx: yes · logo files: brand/acme-logo.svg, brand/acme-logo-white.svg · font files: brand/fonts/Inter-*.ttf
Brand lock (only without design guide): not needed, design guide exists
Product: UI URL + test account: https://atlas.example.com, demo account "demo-site-7" · click path: open site → take 3 photos → record 20 s memo → tap "Report" → review → send · screen recordings: none yet · product images: brand/atlas-phone.png
Voice: keynote speaker is the head of product; film VO English, calm female or male voice, no accent preference · music: licensed library only, no vocals

## Constraints

Legal lines: no claims about legal compliance of reports; "EU hosting" only with the data-centre location named
Claims not allowed: comparisons naming competitors; "40% faster" until measured (E3)
Deadline: trade fair keynote in 8 weeks; film live on the landing page one week before
Budget for generated footage: 600 EUR

## Story hints

Only from sources or the owner's words; the narrative decides.
Villain candidate: the evening pile: "47 photos, 3 voice memos, zero report" (from interviews.md)
Promise candidate: the report is done before you leave the site (from prfaq.md)

## Open points

| Field or evidence | What is missing | Who can close it |
|---|---|---|
| E3 | no measurement behind "40% faster"; drop or run a timed comparison | product lead |
| E5 | baseline is self-reported; a measured baseline would make it solid | pilot coordinator |
| Product · screen recordings | none yet; needed for the demo beat in the films | product designer |
