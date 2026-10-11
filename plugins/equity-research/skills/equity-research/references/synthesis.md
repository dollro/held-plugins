# Synthesis: Investor Lens Consensus, Scenarios and Analyst Instincts

How the team lead turns the five specialist outputs into the final report, after the scoring summary, IAS, red-flag gate and verdict from `SKILL.md` are done. Covers the explicit **Overpriced or Underpriced?** verdict, the bull/base/bear scenarios, the executive summary, and the instincts to apply while writing. The report layout itself is in `report-template.md`; agent numbers refer to `agent-prompts.md`.

## Investor Lens Consensus — Overpriced or Underpriced?

This is a **critical synthesis section** that combines the Buffett and Wood lenses with the scorecard valuation to produce an explicit pricing verdict. Include this as a dedicated section in the final report.

**Compile the Investor Lens table:**

| Lens | Signal | Confidence | Key Reasoning |
|-|-|-|-|
| **Scorecard (IAS)** | [Verdict from IAS] | IAS score | [1-line: scorecard rationale] |
| **Buffett Value** | [from Agent 4] | X% | [1-line: margin of safety? quality?] |
| **Wood Innovation** | [from Agent 5] | X% | [1-line: growth? disruption?] |
| **6mo Price Action** | [derived below] | — | [1-line: where in range?] |

**Derive the 6-Month Price Positioning verdict** (from Agents 4+5 data):
- Both agents report 6mo high, 6mo low, current position %, and 6mo return.
- Classify position:
  - **0–25% of range:** Near 6mo lows → potentially underpriced if fundamentals intact
  - **25–75% of range:** Mid-range → neutral price positioning
  - **75–100% of range:** Near 6mo highs → potentially overpriced or momentum-driven

**Derive the OVERPRICED / UNDERPRICED / FAIRLY PRICED verdict:**

Cross-reference ALL signals:

| Combination | Verdict |
|-|-|
| Buffett says undervalued (margin of safety > 15%) + Price near 6mo lows | **UNDERPRICED** — Value opportunity |
| Buffett says undervalued + Price near 6mo highs | **FAIRLY PRICED** — Good business but market catching on |
| Buffett says overvalued + Wood says bullish (high growth) | **GROWTH-PRICED** — Expensive by value metrics but growth may justify |
| Buffett says overvalued + Wood says neutral/bearish | **OVERPRICED** — Neither value nor growth justifies current price |
| Both bullish + Price near 6mo lows | **STRONGLY UNDERPRICED** — Rare consensus opportunity |
| Both bearish + Price near 6mo highs | **STRONGLY OVERPRICED** — Avoid / consider exit |
| Mixed signals + Mid-range price | **FAIRLY PRICED** — Market pricing about right |

Write a **2-3 paragraph "Overpriced or Underpriced?" section** for the final report that synthesizes:
1. The Buffett margin of safety calculation (intrinsic value vs. market cap)
2. The Wood growth assessment (is high growth priced in, or is there upside?)
3. The 6-month price action (where in the recent range? momentum or reversal?)
4. The scorecard's Chapter 2 valuation scores
5. A clear, unambiguous conclusion: **OVERPRICED / UNDERPRICED / FAIRLY PRICED / GROWTH-PRICED**

## Construct Bull / Base / Bear Scenarios

Using the combined intelligence from all 5 agents:
- **Bull (15-30%):** Use optimistic metrics from Agent 1, best catalysts from Agent 2, Wood's growth thesis from Agent 5.
- **Base (45-60%):** Consensus path. Current trajectory continues. Buffett's conservative DCF as anchor.
- **Bear (15-30%):** Key risks from Agent 3, Buffett's concerns from Agent 4, competitive threats from Agent 2.
- Calculate probability-weighted price target.
- Chance/Risk Ratio = (Bull upside% × prob + Base upside% × prob) / (Bear downside% × prob)

## Write the Executive Summary

Lead with verdict and conviction. Core thesis. Single biggest risk. Include the overpriced/underpriced conclusion prominently. 2–3 paragraphs a PM can read in 2 minutes.

## Analyst Instincts (apply during synthesis)

**Scorecard Instincts:**
- Revenue growth without margin expansion is a treadmill. Growth with improving unit economics is the signal.
- ROIC > WACC is the single most important value creation indicator.
- Consensus embeds expectations. The question: will they grow MORE or LESS than expected?
- Management guidance is marketing. Look at actions (buybacks, insider buys, capex), not words.
- "No competitors" is always wrong. Who else solves the pain point?
- Best investments often have a narrative problem — screen says one thing, story says another. Find the gap.

**Buffett Instincts:**
- A wonderful company at a fair price beats a fair company at a wonderful price.
- If Buffett says BEARISH but Wood says BULLISH — the stock is likely a growth play with high execution risk. Flag this tension explicitly.
- Margin of safety is non-negotiable for Buffett. If intrinsic value < market cap, it's overpriced regardless of growth story.
- Owner earnings > reported earnings as the true measure of cash generation.
- Book value per share growth is the compound wealth engine. BVPS CAGR > 15% for 5+ years = compounder.

**Wood Instincts:**
- Innovation creates its own demand. TAM estimates are usually too small for true disruptors.
- If Wood says BULLISH but Buffett says BEARISH — the stock is a high-growth bet that traditional value frameworks can't capture. Flag this tension.
- Growth deceleration is the kill signal. Two consecutive quarters of slowing growth = thesis at risk.
- Gross margin > 60% in a fast-growing company = software/platform economics = durable advantage.
- For disruptors, EV/Revenue may be more relevant than P/E because earnings are intentionally depressed by growth investment.

**Pricing Instincts:**
- When BOTH Buffett and Wood agree → high conviction signal (rare and powerful).
- When they DISAGREE → the stock is in a "style transition zone." Explicitly state which framework applies better to this company.
- 6-month price at top of range + overvalued on fundamentals = classic OVERPRICED signal.
- 6-month price at bottom of range + undervalued on fundamentals = classic UNDERPRICED signal.
- High short interest + improving fundamentals + approaching catalyst = powerful setup (regardless of lens).
