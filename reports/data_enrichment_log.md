# Data Enrichment Log

Documents all additions made to the starter dataset for Task 1 (Data Exploration & Enrichment).
Enriched files: `data/processed/ethiopia_fi_unified_data_enriched.csv`, `data/processed/impact_links_enriched.csv`

**Collected by:** Meklit
**Collection date:** 2026-07-17 to 2026-07-18

## Why these additions

Exploration of the starter dataset (see `notebooks/01_schema_understanding.ipynb`) showed strong
coverage of ACCESS and USAGE, but QUALITY, TRUST, and DEPTH had zero observations, and AFFORDABILITY
had only one. All additions below target those specific gaps using real, cited sources, no
fabricated or rounded values.

**Correction (2026-07-18):** an earlier version of this log incorrectly stated that EVT_0007 and
EVT_0008 had zero impact_links. Verified directly against `data/raw/impact_links.csv`: EVT_0007
already had 2 links (IMP_0011, IMP_0012) and EVT_0008 already had 1 (IMP_0013) in the original data.
The events that actually had **zero** impact_links were **EVT_0006** (P2P Surpasses ATM) and
**EVT_0009** (NFIS-II Strategy Launch) — both are the ones addressed by IMP_0018 and IMP_0019 below.
IMP_0015/IMP_0016 (added to EVT_0007/EVT_0008) are still valid, sourced additions. They just add a
second/third link to already-linked events rather than filling a true zero-coverage gap. Nothing was
removed; only this explanation is corrected. Always verify claims like "X has zero links" directly
against the data (`df.groupby('parent_id').size()`) rather than trusting an earlier summary.

**Note on IDs:** REC_0031-0033 collided with the three pre-existing `target` records that already used
those IDs. This has been fixed, the affected observations were renumbered to REC_0044-0046. If you
pulled a copy of the enriched CSV before this fix, re-download it.


## New Observations (11)

### ACCESS

**REC_0034 / REC_0035: Mobile Money Agent Count**
- 22,725 agents (FY2019/20) → 415,084 agents (FY2023/24), ~18x growth
- Source: DFS Ethiopia Hub (Shega): https://digitalfinance.shega.co/insights/articles/the-rise-of-mobile-money-in-ethiopia-without-the-agents
- Confidence: medium (counts registrations, not active agents: see REC_0046)
- Notes: direct ACCESS correlate per Additional Data Points Guide sheet B (agent distribution)

**REC_0036: Electricity Access Rate**
- 55.4% of population (2023)
- Source: World Bank Development Indicators: https://data.worldbank.org/indicator/EG.ELC.ACCS.ZS?locations=ET
- Confidence: high
- Notes: indirect/enabling correlate (Guide sheet C); electricity underpins agent uptime, device
  charging, and network reliability

### TRUST (previously zero observations)

**REC_0037: Banking Sector Fraud Losses**
- 1.3 billion ETB (FY ending June 2024), 28 of 31 banks affected
- Source: NBE Financial Stability Report, via Capital Market Ethiopia:  https://www.capitalmarketethiopia.com/28-ethiopian-banks-lose-1-3-billion-birr-to-fraud/
- Confidence: high
- Notes: rising fraud is a direct headwind against trust-driven usage growth; should be modeled as
  a constraining factor

**REC_0038: Cyberattack Attempts (H1 2024)**
- 4,623 attempts, +115% YoY
- Source: NBE, via The Reporter Ethiopia : https://www.thereporterethiopia.com/48123
- Confidence: high
- Notes: cited in NBE's own draft National Digital Payments Strategy (NDPS 2.0) as a key sector risk

### QUALITY (previously zero observations)

**REC_0039: Mobile Money Account Active Rate (National, all providers)**
- 15% of ~140 million registered accounts active
- Source: NBE draft NDPS 2.0, via The Reporter Ethiopia : https://www.thereporterethiopia.com/48123
- Confidence: medium (draft strategy document, not finalized)
- **Important:** do not treat this as contradicting REC_0025 (USG_ACTIVE_RATE = 66%, 2024-12-31).
  That figure is a single-platform 90-day active rate; this one is NBE's national, all-provider,
  all-time-registered count. Different scope, both valid — noted so no one "corrects" one using the other.

**REC_0046 : Mobile Money Agent Activity Rate**
- 42% of newly recruited agents active (end of 2023, up from 17% baseline in 2022)
- Source: UNCDF Ethiopia : https://www.uncdf.org/article/9050/how-agent-networks-are-powering-change-in-ethiopia
- Confidence: medium (covers one operator partnership, not confirmed national)
- Notes: shows whether the agent network in REC_0034/35 actually functions, not just its registered size

### GENDER

**REC_0040 / REC_0041 : Adults Lacking Mobile Money Skills, by gender**
- Female: 66% | Male: 60% (6pp digital-skills gap)
- Source: NBE draft NDPS 2.0 : https://nbe.gov.et/ndps/
- Confidence: medium
- Notes: a new, distinct GENDER indicator (digital literacy) alongside the existing account-ownership
  gap (GEN_GAP_ACC) a specific, actionable barrier rather than a restatement of ownership stats

### AFFORDABILITY (previously only 1 observation)

**REC_0042 :  Mobile Broadband Basket Cost, 2017**
- ~12% of monthly GNI per capita
- Source: GSMA, via AfricanWirelessComms :  https://www.africanwirelesscomms.com/news-details?itemid=8511
- Confidence: medium ("nearly 12%" is an approximation in the source)

**REC_0043 : Mobile Broadband Basket Cost, 2022**
- 3.4% of monthly GNI per capita
- Source: British International Investment, citing ITU DataHub :  https://assets.bii.co.uk/wp-content/uploads/2024/10/09105903/BII-Impact-of-investment-in-the-Ethiopian-telecoms-market_2024.pdf
- Confidence: high
- Notes: together with REC_0042 and the existing REC_0026 (2%, 2024), this turns AFFORDABILITY from a
  single snapshot into a real 3-point trend: 2017 (~12%) → 2022 (3.4%) → 2024 (2%)

### DEPTH (previously zero observations)

**REC_0044 : Formal Saving Rate**
- 36% of adults (2024)
- Source: World Bank Global Findex 2025, via Birr Metrics — https://birrmetrics.com/49-of-ethiopians-are-banked-as-findex-2025-highlights-the-next-inclusion-challenge/
- Confidence: high

**REC_0045: Formal Borrowing Rate**
- 4% of adults (2024)
- Source: same as above
- Confidence: high
- Notes: very low formal credit penetration also flagged as a standing market nuance in the
  Additional Data Points Guide (sheet D)


## New Events (1)

**EVT_0011: ASCENT Ethiopia Electrification Program Approval**
- Category: infrastructure | Date: 2025-07-29
- Source: World Bank press release : https://www.worldbank.org/en/news/press-release/2025/08/04/new-world-bank-program-to-expand-electricity-access-to-six-million-people-across-ethiopia
- Confidence: high
- Notes: $424M program ($400M IDA credit + $24M Denmark grant). Pillar deliberately left empty per
  schema rule. Linked via IMP_0017.


## New Impact Links (5)

**IMP_0015 : EVT_0007 (M-Pesa–EthSwitch Integration) → USAGE / USG_P2P_COUNT**
- increase / medium magnitude, 6-month lag | evidence: theoretical | confidence: estimated
- EVT_0007 already had 2 impact_links (IMP_0011, IMP_0012); this adds a third pathway. Reasoned estimate, not a measured effect.

**IMP_0016 : EVT_0008 (EthioPay Instant Payment Launch) → USAGE / USG_P2P_COUNT**
- increase / medium magnitude, 6-month lag | evidence: theoretical | confidence: estimated
- EVT_0008 already had 1 impact_link (IMP_0013); this adds a second pathway. Reasoned estimate, not a measured effect.

**IMP_0017 : EVT_0011 (ASCENT Electrification) → ACCESS / ACC_MM_ACCOUNT**
- increase / low magnitude, 24-month lag, relationship: enabling | evidence: theoretical | confidence: estimated
- Longer lag reflects multi-year rollout; indirect pathway via agent uptime and device charging.

**IMP_0018 : EVT_0006 (P2P Surpasses ATM) → USAGE / USG_CROSSOVER**
- stabilize / medium magnitude | evidence basis and confidence: high
- EVT_0006 had zero impact_links despite already being a milestone event in the dataset.

**IMP_0019 : EVT_0009 (NFIS-II Strategy Launch) → ACCESS / ACC_OWNERSHIP**
- increase / medium magnitude | confidence: estimated
- EVT_0009 (a 2021 policy launch) had zero impact_links; national strategy launches plausibly drive
  account ownership over the following years.


## Round 2 additions : turning TRUST and QUALITY into real trends

The first enrichment pass gave TRUST and QUALITY a single data point each, enough to not be empty,
not enough to show direction. This pass adds a second, earlier point to each so they're proper
2-point trends instead of snapshots, plus one new event tying them together.

### REC_0047 : Banking Sector Fraud Losses (TRUST), FY2022/23
- 1.0 billion ETB
- Source: NBE Financial Stability Report, via Birr Metrics : https://birrmetrics.com/ethiopia-banks-hit-by-1-3-bln-birr-in-fraud-as-third-party-risks-climb-central-bank-warns/
- Confidence: high
- Notes: prior-year point for REC_0037 (1.3bn, FY2023/24). Together they show a 30% YoY rise in
  fraud losses, a real trend, not a snapshot.

### REC_0048 : Mobile Money Agent Activity Rate (QUALITY), 2022 baseline
- 17% of agents active
- Source: UNCDF Ethiopia : https://www.uncdf.org/article/9050/how-agent-networks-are-powering-change-in-ethiopia
- Confidence: medium
- Notes: 2022 baseline for REC_0046 (42%, end of 2023), same source/program. Shows activity roughly
  2.5x'd in a year but both points are from the same pilot (Highlight Trading), so treat as
  program-level evidence, not a confirmed national trend.

### EVT_0012 : CBE Core Banking System Glitch
- Category: infrastructure | Date: 2024-03-16
- Source: Wikipedia, aggregating BBC/Euronews/Addis Standard : https://en.wikipedia.org/wiki/2024_Commercial_Bank_of_Ethiopia_glitch_incident
- Confidence: high
- Notes: a system malfunction at Ethiopia's largest bank let customers withdraw beyond their
  balances for several hours before containment. Pillar left empty per schema. Linked via IMP_0020.

### IMP_0020 : EVT_0012 → TRUST / TRUST_FRAUD_LOSS
- decrease (i.e., worsens trust standing) / medium magnitude, 1-month lag
- Evidence basis: empirical (widely reported) | Confidence: medium
- Notes: high-profile incident at a bank holding 60%+ of national deposits and 38M account holders
  plausibly dented public trust in digital banking reliability in the following months.


## Summary

| Type | Added (total) | New total |
|---|---|---|
| Observations | 13 | 43 |
| Events | 2 | 12 |
| Impact links | 6 | 20 |
| Targets | 0 | 3 |

## Data quality note (fixed in round 1)
A record_id collision was found and corrected: three new observation rows had accidentally reused
IDs (REC_0031-0033) already assigned to the dataset's original `target` records. Renumbered to
REC_0044-0046. Always check `df['record_id'].duplicated()` after merging enrichment batches, this
check is now run automatically before every save.

## Pillars still needing attention
All seven pillars now have at least one observation, and TRUST/QUALITY now have real 2-point trends
rather than single snapshots. Remaining honest limitation: most non-ACCESS/USAGE pillars still have
too few points (2-3) to fit a proper time-series model, treat them as directional context for the
forecast rather than standalone forecast inputs at this stage.