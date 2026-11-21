"""Worked example, keynote mode: a product launch for a fictional product.
Run: python keynote_example.py [template.pptx]  ->  keynote_example.pptx
Without a template: black stage. With a template: the master's background, logo and fonts stay;
pass stage="dark" to new_deck for a dark stage on the template's layouts.

Arc (sparkline): what is (the pain) -> what could be (the promise) -> reveal -> three things ->
proof (one number per slide, fine print) -> what is vs what could be -> close with availability.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from deckkit import *  # noqa: E402,F403

template = sys.argv[1] if len(sys.argv) > 1 else None
prs = new_deck(template, mode="keynote")
FP = "Illustrative example · Fictional product and test data"

s = title_slide(prs, "Field notes, finally", "Product launch · 2027", note=FP)

s = statement(prs, "Every site visit ends the same way.")
notes(s, "Open with the moment everyone in the room knows: the drive home, the half-remembered visit.")

s = statement(prs, "47 photos. 3 voice memos. [[Zero]] report.")
notes(s, "This is the villain: the report that never gets written. Pause after 'zero'.")

s = big_number(prs, "6.5 h", "per week writing up site visits", context="for a typical field engineer",
               fine_print="Illustrative figure. Fictional survey of 120 field engineers, 2026.")
notes(s, "Make the cost concrete. 6.5 hours is most of a working day, every week.")

s = statement(prs, "What if the report [[wrote itself]]?")
notes(s, "The turn from what is to what could be. Let it sit for two seconds.")

s = image_slide(prs, caption="Fieldbook", placeholder="Product shot: Fieldbook on a phone, on site")
notes(s, "The reveal. Say the name once, then stop talking.")

slides = reveal(prs, "Three things", ["Capture anything", "Understands context", "Report in one tap"])
for sl, line in zip(slides, ["Photos, voice, sketches.", "Knows the site, the asset, the history.",
                             "Draft ready before you reach the car."]):
    notes(sl, line)

s = three(prs, "Built for the field", [("Offline", "No signal needed"), ("Private", "Data stays local"),
                                       ("Open", "Exports anywhere")])
notes(s, "Answer the three objections before anyone raises them.")

s = versus(prs, "From visit to report", ("Today", "2 days", "Typed up at the office"),
           ("With Fieldbook", "4 min", "Sent from the site"),
           fine_print="Illustrative. Median of 40 fictional test visits, 2026.")
notes(s, "Old way on the left, new way on the right. Read the two numbers, nothing else.")

s = keynote_chart_slide(prs, "Time back, every week", sub="Hours per engineer per week")
bar_chart(s, ["Before", "Week 1", "Week 4", "Week 12"], [6.5, 4.0, 2.1, 1.2], highlight=3, horizontal=False,
          number_format="0.0", x=2.0, y=2.3, w=9.3, h=4.2)
fine(s, "Illustrative. Fictional pilot, 3 teams, 2026.")
illustrative(s)
notes(s, "The curve does the talking: it keeps falling as the system learns the site.")

s = quote(prs, "I finished the report before I finished my coffee.", "Pilot user (fictional)")
notes(s, "Only real, attributable quotes in a real deck.")

s = closing(prs, "Available today", details=["Free for teams up to 5", "€12 per user per month after that"],
            cta="fieldbook.example")
notes(s, "Close on how to start. No 'Questions?' slide.")

out = os.path.join(os.getcwd(), "keynote_example.pptx")
prs.save(out)
print("saved", out)
