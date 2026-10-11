# Analyst Checklist — Chapters 5 & 6: Management + Risk Assessment

> What to pull from MCP, what to search, how to assess.

---

## Chapter 5: Management & Capital Allocation

### 5.1–5.4 — All Management Criteria

**MCP calls:**
- `get_holder_info(type: insider)` → Insider buying/selling patterns. Net buying = positive.
- `get_holder_info(type: institutional)` → Top holders. Increasing institutional ownership = smart money.
- `get_stock_actions` → Dividend history, splits — capital return consistency.
- `get_financial_statement(cashflow)` → Buyback and dividend amounts.

**Web search:**
- "[Company] CEO track record" or "[CEO name] track record"
- "[Company] capital allocation" — deployment strategy
- "[Company] M&A history" — acquisition track record
- "[Company] corporate governance" — board composition, shareholder rights
- "[Company] insider buying [year]" — recent transactions
- "[Company] executive compensation" — alignment

**Key questions:**
- **Track record:** Consistently delivered on guidance? Beats = conservative (positive). Misses = credibility problem.
- **Capital allocation:** Buybacks well-timed? M&A accretive (ROIC > WACC)? R&D yielding returns?
- **Insider signals:** Net buying = strongest predictive signal. Cluster selling by multiple insiders = warning.
- **Governance:** Dual-class = discount. Related-party = red flag.

---

## Chapter 6: Risk Assessment

### 6.1–6.4 — All Risk Criteria

**MCP calls:**
- `get_stock_info` → Beta, sector (cyclicality indicator)
- `get_historical_stock_prices(5y, 1wk)` → Max drawdown during 2020 COVID, 2022 rate hikes
- `get_financial_statement(income_stmt)` → Revenue volatility through cycles
- `get_yahoo_finance_news` → Risk-relevant news (lawsuits, regulatory)

**Web search:**
- "[Company] 10-K risk factors" — management risk disclosure
- "[Company] litigation" or "[Company] lawsuits"
- "[Company] regulatory risk" — regulatory environment
- "[Company] customer concentration" — top customer dependency
- "[Company] supply chain risk" — single-source suppliers
- "[Company] ESG rating" or "[Company] ESG controversies"
- "[Company] cybersecurity" — breach history

**Key questions:**
- **Macro:** Revenue/earnings during 2020 downturn? 2022 rate hikes? Historical stress reveals exposure.
- **Regulatory:** Pending legislation impacting business model? Antitrust? Sector-specific regulation?
- **Concentration:** Any customer > 10%? Single-geography with geopolitical risk? Single-source supplier?
- **Tail risk:** Worst realistic scenario? Existential risk credible?
- **10-K risk factors:** Specific (not boilerplate), newly added, or notably longer than peers = management is worried.

**Risk matrix output format:**

| Risk Factor | Probability | Severity | Mitigation | Monitoring Trigger |
|-|-|-|-|-|
| [Risk 1] | H/M/L | H/M/L | [Company mitigation] | [What to watch] |
| [Risk 2] | H/M/L | H/M/L | [Company mitigation] | [What to watch] |
| [Risk 3] | H/M/L | H/M/L | [Company mitigation] | [What to watch] |
| [Risk 4] | H/M/L | H/M/L | [Company mitigation] | [What to watch] |

**Stress test (apply to the most relevant scenario):**
- Mild recession (−10% revenue): Stressed EBITDA, interest coverage, cash runway
- Severe recession (−25% revenue): Covenant triggers, capital raise risk
- Competitive disruption (−15% permanent): Impact on intrinsic value
