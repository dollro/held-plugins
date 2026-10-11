# Scoring Criteria — Chapters 5 & 6: Management + Risk Assessment

> Score [1–5]. Score reflects the **weaker** of sub-dimensions.

---

## Chapter 5: Management & Capital Allocation (Weight: 10%)

### 5.1 — Management Track Record & Credibility [1–5]

**What it measures:** History of executing against goals, delivering on guidance, navigating challenges.

| Score | Criteria |
|:-:|-|
| 5 | Exceptional execution. Consistently meets/beats guidance. Successfully navigated past challenges. Industry respect. |
| 4 | Good track record with occasional well-explained misses. Relevant prior experience. |
| 3 | Mixed — some hits, some misses. Guidance accuracy ±5%. |
| 2 | Multiple guidance cuts or missed targets in past 2 years. Credibility eroding. Leadership uncertainty. |
| 1 | Serial over-promiser, under-deliverer. Guidance unreliable. Activist pressure or board turmoil. |

---

### 5.2 — Capital Allocation Discipline [1–5]

**What it measures:** How management deploys capital — R&D, M&A, buybacks, dividends, balance sheet.

| Score | Criteria |
|:-:|-|
| 5 | Exceptional allocators. M&A accretive with strong integration. Buybacks at low valuations. R&D yielding returns. |
| 4 | Disciplined. Mostly value-accretive M&A. Reasonable R&D ROI. Sensible buybacks. |
| 3 | Adequate. Reasonable but unspectacular. Some mediocre M&A but not destructive. |
| 2 | Concerns — value-destructive M&A, buybacks at peak, R&D without visible return. |
| 1 | Serial destroyers. Empire-building M&A. Buying back at highs, cutting at lows. ROIC < WACC reflects poor decisions. |

---

### 5.3 — Insider Alignment & Ownership [1–5]

**What it measures:** Skin in the game — insider buying/selling, compensation alignment.

| Score | Criteria |
|:-:|-|
| 5 | Significant ownership (CEO > 3%). Recent open-market buying. Compensation tied to long-term (ROIC, FCF, TSR). |
| 4 | Meaningful ownership. No material selling. Reasonable long-term incentives. |
| 3 | Moderate ownership. Selling limited to 10b5-1 plans. Standard compensation. |
| 2 | Low ownership. Notable selling beyond plans. Compensation tilted short-term. |
| 1 | Minimal ownership. Aggressive selling. Compensation misaligned. Golden parachutes without performance. |

**Data source:** `get_holder_info(type: insider)` for transaction data.

---

### 5.4 — Corporate Governance & Transparency [1–5]

**What it measures:** Board independence, shareholder rights, disclosure quality.

| Score | Criteria |
|:-:|-|
| 5 | Best-in-class. Independent board, no poison pills, annual elections, proxy access, single share class. |
| 4 | Good. Mostly independent. Standard disclosure. Reasonable shareholder rights. |
| 3 | Adequate. Minor concerns (staggered board, limited proxy access) but no deal-breakers. |
| 2 | Concerns — dual-class shares, board not fully independent, related-party transactions. |
| 1 | Poor — entrenched management, controlled board, anti-takeover provisions, related-party issues. |

---

## Chapter 6: Risk Assessment (Weight: 10%)

### 6.1 — Macro & Cyclical Exposure [1–5]

**What it measures:** Sensitivity to economic cycles, rates, currency, macro conditions.

| Score | Criteria |
|:-:|-|
| 5 | Counter-cyclical/non-cyclical. Revenue resilient in downturns. Mission-critical, inelastic demand. |
| 4 | Low cyclicality. Revenue declined < 10% in last recession. Geographic diversification helps. |
| 3 | Moderate. Revenue correlates with GDP but doesn't amplify. Some rate/currency sensitivity. |
| 2 | High cyclicality. Revenue swings 20–30% through cycle. Operating leverage amplifies volatility. |
| 1 | Extreme. Revenue collapses in downturns. Leveraged to commodities, rates, or single currency. |

---

### 6.2 — Regulatory & Legal Risk [1–5]

**What it measures:** Exposure to adverse regulation, litigation, antitrust, policy shifts.

| Score | Criteria |
|:-:|-|
| 5 | Minimal exposure. No material litigation. Stable regulatory framework. Clean compliance. |
| 4 | Some exposure but manageable. Minor litigation. Stable regulatory environment. |
| 3 | Moderate. Potential regulatory changes within 2–3 years. Some litigation but manageable. |
| 2 | Significant. Major regulatory changes proposed/likely. Material litigation ongoing. |
| 1 | Severe. Antitrust action, potential business model disruption, major litigation with material exposure. |

---

### 6.3 — Concentration Risk [1–5]

**What it measures:** Dependence on few customers, suppliers, geographies, or products.

| Score | Criteria |
|:-:|-|
| 5 | Highly diversified. No customer > 5%. No critical single supplier. Strong geo/product diversity. |
| 4 | Good. Largest customer < 10%. Some concentration but manageable. |
| 3 | Moderate. Top customer 10–20% OR > 50% from one region OR key single-supplier dependency. |
| 2 | High. Top customer > 20% OR top 3 > 50%. Single-geography. Critical single supplier. |
| 1 | Extreme. Single customer > 30%. Single product > 80%. Single geography with geopolitical risk. |

---

### 6.4 — ESG & Tail Risk [1–5]

**What it measures:** Environmental, social, governance tail risks that could cause sudden value destruction.

| Score | Criteria |
|:-:|-|
| 5 | ESG leader. Strong cybersecurity. Minimal environmental liabilities. Diversified operations. |
| 4 | Good ESG. Manageable environmental exposure. Standard cybersecurity. Low tail risk. |
| 3 | Average ESG. Some exposure within industry norms. Normal tail risk. |
| 2 | Below-average. Material environmental liabilities, labor controversies. Elevated tail risk. |
| 1 | ESG red flags. Major liabilities/controversies that could cause sudden value destruction. |
