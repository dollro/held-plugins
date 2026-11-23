"""Worked example, keynote built from a story-craft narrative, with clips from motion-craft.
Run: python atlas_keynote.py [clips.json] [--template brand.pptx]  ->  atlas_keynote.pptx

The slides follow story-craft/examples/atlas/storyboard.md (cut keynote, one slide per beat).
With a clips.json (motion-craft:motion-qa export), the villain beat B02 and the STAR beat B12
play their film clips via video_slide_from_clips(); without one, they fall back to a statement.
Fictional product and sample data.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from deckkit import *  # noqa: E402,F403

args = [a for a in sys.argv[1:] if not a.startswith("--")]
template = sys.argv[sys.argv.index("--template") + 1] if "--template" in sys.argv else None
args = [a for a in args if a != template]
clips = args[0] if args else None

prs = new_deck(template, mode="keynote")
FP = "Illustrative example · Fictional company (Acme) and sample data"


def clip_or_statement(beat, words, spoken):
    if clips:
        s = video_slide_from_clips(prs, clips, beat)
    else:
        s = statement(prs, words)
    return notes(s, spoken)


title_slide(prs, "Site reports, finally done on site.", "atlas · product launch", note=FP)

notes(statement(prs, "Every site visit ends the [[same way]]."),                                      # B01
      "Every site visit ends the same way. You walk back to the car with a full phone.")
clip_or_statement("B02", "47 photos. 3 voice memos. [[Zero]] report.",                               # B02
                  "Forty-seven photos. Three voice memos. And not one line of the report. (pause)")
s = big_number(prs, "6.5 h", "a week on site reports", context="most of a working day, every week",  # B03
               fine_print="Median, survey of 120 site managers. Illustrative data.")
notes(s, "Site managers told us: six and a half hours a week. Most of a working day, every week.")
notes(statement(prs, "Friday, 9 pm. Still writing up [[site 3]]."),                                  # B04
      "And it lands on Friday evening, when everyone else has gone home.")
notes(statement(prs, "What if the report was done [[before you left]]?"),                           # B05
      "So we asked: what if the report was done before you left the site? (pause)")
notes(image_slide(prs, caption="atlas", placeholder="Product shot: atlas on a phone, on site"),      # B06
      "This is atlas. (pause, two seconds)")
for sl, line in zip(reveal(prs, "atlas", ["Capture anything", "Understands the site", "Report in one tap"]),
                    ["Photos, voice, a sketch on a plan.", "Which room, which trade, which defect.",
                     "And the report is one tap away."]):                                            # B07-B09
    notes(sl, line)
s = big_number(prs, "9 in 10", "pilot reports sent the same day", context="before: about 1 in 4",    # B10
               fine_print="Pilot, 14 site managers, 6 weeks. Illustrative data.")
notes(s, "In our pilot, nine out of ten reports went out the same day.")
s = big_number(prs, "72 h", "offline, nothing lost", context="sync when the signal is back",          # B11
               fine_print="Internal test protocol T-12, 3 devices. Illustrative data.")
notes(s, "No signal in the basement? Seventy-two hours offline in our tests. Not one entry lost.")
clip_or_statement("B12", "Three photos. One memo. [[Report done.]]",                                 # B12 STAR
                  "Let me show you. Three photos, one memo, one tap. You check it, you send it. Done.")
notes(three(prs, "Built for your site", [("Your template", "fills your own report form"),             # B13
                                         ("Your data", "stays yours"),
                                         ("Per site", "not per seat")]),
      "Your template, your data, and you pay per site, not per person.")
notes(versus(prs, "Pilot: time on reports", ("Before", "6.2 h", "a week, estimated"),                # B14
             ("With atlas", "1.4 h", "a week, estimated"),
             fine_print="Pilot users' estimates, self-reported baseline. Illustrative data."),
      "Pilot users estimated about six hours a week before, under one and a half after.")
notes(quote(prs, "I sent the report from the car park.", "Site manager, mid-size builder (pilot)"),  # B15
      "One pilot user said: I sent the report from the car park. First time in ten years.")
notes(statement(prs, "Home on time on [[Friday]]."), "Friday evening is yours again.")               # B16
notes(closing(prs, "Free pilot. One site. 30 days.", details=["Start with the site you visit most"],  # B17
              cta="atlas.example.com"),
      "Start a free pilot on one site for thirty days. atlas.example.com.")

out = os.path.join(os.getcwd(), "atlas_keynote.pptx")
prs.save(out)
print("saved", out, "with clips" if clips else "without clips")
