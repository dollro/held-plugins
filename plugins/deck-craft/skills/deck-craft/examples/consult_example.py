"""Worked example, consult mode: a 10-slide steering-committee deck with fictional data.
Run: python consult_example.py  ->  consult_example.pptx
Shows: cover, executive summary with ask, divider, ranking bar + callout, waterfall + annotation,
2x2, MECE columns, options table, next steps. Every data slide is labelled Illustrative.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from deckkit import *  # noqa: E402,F403

prs = new_deck(mode="consult")          # new_deck("brand.potx", mode="consult") for a corporate master
set_sections(["Diagnosis", "Options", "Plan"])
SRC = "Source: client finance data (FY2023-25), as provided in brief; team analysis"

title_slide(prs, "Restoring wholesale margin", "Steering committee · 12 November 2026",
            note="Illustrative example · Fictional company and sample data")

s = content_slide(prs, "Repricing café-chain contracts recovers 5 of the 6 lost margin points by FY2027")
exec_summary(s, [
    ("What happened", "Wholesale gross margin fell from 34% to 28% in two years."),
    ("Why", "Café chains drive two thirds of the decline: green coffee rose 38%, their prices 9%."),
    ("What to do", "Reprice the 12 chain contracts at renewal and add a coffee-cost escalator."),
    ("What it is worth", "+5 margin points, about €4.1M gross profit a year, at 8% volume risk."),
], ask="Decision today: mandate sales to open repricing talks with the top 6 chains in Q1")
illustrative(s)
source(s, SRC)

divider_slide(prs, "Diagnosis", "Café chains, not grocery, explain most of the margin loss", number=1)

s = content_slide(prs, "Café chains drive most of the decline: their margin fell 9 points", section="Diagnosis")
bar_chart(s, ["Café chains", "Independent cafés", "Grocery", "Online"], [-9.0, -4.0, -3.0, 1.0],
          highlight=0, w=8.3, unit="Change in gross margin, FY2023-25, percentage points",
          number_format='+0.0;-0.0')
callout(s, "So what", ["Chains are 45% of wholesale volume", "Their contracts reprice once a year",
                       "No cost pass-through clause today"])
illustrative(s)
source(s, SRC)

s = content_slide(prs, "Green coffee costs took 7.5 points of margin; price rises returned only 2.5",
                  section="Diagnosis")
waterfall(s, [("FY2023", 34.0, "total"), ("Green coffee", -7.5, "delta"), ("Freight", -1.0, "delta"),
              ("Mix", -0.5, "delta"), ("Price", 2.5, "delta"), ("Other", 0.5, "delta"),
              ("FY2025", 28.0, "total")], w=8.3, unit="Wholesale gross margin bridge, %")
callout(s, "So what", ["Price rises covered a third of the cost shock", "Freight and mix are small; ignore them",
                       "The fix is price, not cost"])
illustrative(s)
source(s, SRC)

divider_slide(prs, "Options", "Repricing beats volume growth and cost cutting on value and speed", number=2)

s = content_slide(prs, "The top 6 chains combine high volume with low margin: start there", section="Options")
matrix_2x2(s, ("Low", "High", "Share of wholesale volume"), ("Low", "High", "Gross margin"),
           [("Protect", "Independents, specialty: keep service level"),
            ("Grow", "Online subscriptions: invest in reach"),
            ("Exit or fix", "Small grocery accounts: minimum order"),
            ("Reprice first", "Top 6 café chains: 38% of volume at 22% margin")],
           highlight=3)
callout(s, "Implication", ["Six negotiations carry most of the value", "All six renew within 9 months"],
        x=9.13, w=3.7)
illustrative(s)
source(s, SRC)

s = content_slide(prs, "Three levers exist; repricing is the only one that pays back within a year",
                  section="Options")
columns(s, [("Reprice", ["+5.0 pts margin", "Payback < 6 months", "Risk: 8% volume"]),
            ("Grow volume", ["+1.0 pt via scale", "Payback 2-3 years", "Risk: capex"]),
            ("Cut cost", ["+1.5 pts margin", "Payback 12 months", "Risk: service level"])],
        highlight=0, band="Combined potential: up to 7.5 points if all three run")
illustrative(s)
source(s, SRC)

s = content_slide(prs, "Repricing with an escalator scores best on value, speed and risk", section="Options")
table(s, ["Option", "Margin effect", "Time to effect", "Volume risk", "Verdict"],
      [["A  Status quo", "-1 pt/yr", "-", "None", "Reject"],
       ["B  Reprice + escalator", "+5.0 pts", "2-3 quarters", "~8%", "Recommend"],
       ["C  Reprice only", "+3.5 pts", "2-3 quarters", "~10%", "Fallback"],
       ["D  Exit chains", "+2.0 pts", "4 quarters", "45%", "Reject"]],
      col_widths=[3.4, 2.2, 2.4, 2.0, 2.333], highlight_row=1)
illustrative(s)
source(s, SRC)

divider_slide(prs, "Plan", "Six negotiations in two waves, decided by end of Q2", number=3)

s = content_slide(prs, "Decide today, open talks in January, close all six contracts by June 2027",
                  section="Plan")
next_steps(s, [("Approve repricing mandate and escalator clause", "Steering committee", "Today"),
               ("Prepare account packs for top 6 chains", "Head of key accounts", "19 Dec"),
               ("Wave 1 talks: chains 1-3", "Sales director", "Mar 2027"),
               ("Wave 2 talks: chains 4-6", "Sales director", "Jun 2027"),
               ("Track volume and margin monthly", "Finance", "From Jan")])
source(s, "Source: team plan")

out = os.path.join(os.getcwd(), "consult_example.pptx")
prs.save(out)
print("saved", out)
