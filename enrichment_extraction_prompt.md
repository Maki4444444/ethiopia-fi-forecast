# Data Enrichment Extraction Prompt

Use this prompt (with an AI assistant, or as a manual checklist) against each source below to pull
new observations, events, and impact_links for the Ethiopia Financial Inclusion dataset. Run it once
per source, don't combine sources in a single pass, or citations get muddled.


## The Prompt

```
You are helping enrich a structured dataset on Ethiopia's financial inclusion (Access, Usage,
Affordability, Gender, Quality, Trust, Depth). I will give you a source (a URL, report, or document).

Extract any data points from this source that fit ONE of these three record types. Do not invent,
estimate, or round numbers you don't see explicitly stated. If the source has nothing relevant,
say so and stop.

1. OBSERVATION a real measured value about Ethiopia. For each one found, return:
   - pillar: one of ACCESS | USAGE | AFFORDABILITY | GENDER | QUALITY | TRUST | DEPTH
   - indicator: short human-readable name (e.g. "Formal Saving Rate")
   - indicator_code: short snake/caps code, prefixed by pillar abbreviation
     (e.g. ACC_, USG_, AFF_, GEN_, QUAL_, TRUST_, DEPTH_)
   - value_numeric: the number itself
   - value_type: percentage | count | currency_etb | currency_usd | ratio | rate | index | gap_pp
   - observation_date: the date the figure refers to (not the publish date, if different)
   - gender: all | male | female (only if the source disaggregates by gender)
   - location: national | urban | rural
   - source_name: name of the publishing org
   - source_url: the exact URL
   - confidence: high (primary source, e.g. World Bank/NBE/IMF direct), medium (credible
     secondary reporting on a primary source), low (unclear provenance)
   - original_text: the exact sentence/quote containing the figure, verbatim
   - notes: one sentence on why this matters for forecasting Access or Usage

2. EVENT something that happened (policy, product launch, market entry, regulation,
   infrastructure, partnership, milestone, economic shock, pricing change) that could plausibly
   affect financial inclusion. Return:
   - category: product_launch | market_entry | market_exit | policy | regulation |
     infrastructure | partnership | milestone | economic | pricing
   - indicator: short event name
   - observation_date: the date it happened
   - source_name / source_url / confidence / original_text (same rules as above)
   - Do NOT assign a pillar to events. Leave it out entirely — this is a strict schema rule.

3. IMPACT_LINK only if the source explicitly states or strongly implies that a specific event
   affected a specific indicator. Return:
   - parent_event: name/date of the event it refers to
   - pillar: the affected indicator's pillar
   - related_indicator: which indicator_code it affects (use existing codes where possible:
     ACC_OWNERSHIP, ACC_MM_ACCOUNT, ACC_4G_COV, ACC_MOBILE_PEN, ACC_FAYDA, ACC_AGENT_COUNT,
     ACC_ELECTRICITY, USG_P2P_COUNT, USG_P2P_VALUE, USG_ATM_COUNT, USG_ATM_VALUE, USG_CROSSOVER,
     USG_TELEBIRR_USERS, USG_TELEBIRR_VALUE, USG_MPESA_USERS, USG_MPESA_ACTIVE, USG_ACTIVE_RATE,
     AFF_DATA_INCOME, GEN_GAP_ACC, GEN_MM_SHARE, GEN_GAP_MOBILE, QUAL_AGENT_ACTIVE,
     DEPTH_SAVE_RATE, DEPTH_BORROW_RATE — or propose a new one if none fit)
   - impact_direction: increase | decrease | stabilize | mixed
   - impact_magnitude: high | medium | low | negligible
   - lag_months: estimated time between the event and the effect appearing
   - evidence_basis: empirical (source states a measured effect) | theoretical (source implies
     it but doesn't measure it) | literature | expert
   - confidence: estimated (if you or the source are inferring, not measuring) | otherwise as above

Prioritize the GENDER, AFFORDABILITY, QUALITY, TRUST, and DEPTH pillars — these currently have the
least data. Do not duplicate observations already in the dataset (account ownership 2014/2017/2021/2024,
mobile money account rate 2021/2024, 4G coverage 2023/2025, Fayda enrollment 2024-2025, gender gap
2021/2024) unless you find a more precise or more recent figure for the same indicator.

Output as a markdown table, one row per record, grouped by record type.
```


## Sources to run it against

### Primary data portals (start here, highest confidence)
| Source | Pillar focus | URL |
|---|---|---|
| World Bank Global Findex Database 2025 | ACCESS, USAGE, GENDER, DEPTH | https://www.worldbank.org/en/publication/globalfindex |
| World Bank Findex country page — Ethiopia | ACCESS, USAGE, DEPTH | https://digitalfinance.worldbank.org/country/ethiopia |
| World Bank Open Data — Ethiopia | AFFORDABILITY, ACCESS (infra) | https://data.worldbank.org/country/ethiopia |
| IMF Financial Access Survey (FAS) | ACCESS, GENDER | https://data.imf.org/en/Financial-Access-Survey |
| ITU DataHub | AFFORDABILITY, ACCESS (connectivity) | https://datahub.itu.int/ |
| GSMA | ACCESS, USAGE (mobile money) | https://www.gsma.com/ |
| National Bank of Ethiopia (NBE) | USAGE, QUALITY, TRUST | https://nbe.gov.et/ |
| NBE — Payment Instrument Issuers list | ACCESS, QUALITY | https://nbe.gov.et/payment-instrument-issuers-system-operators/ |
| G20 Financial Inclusion Indicators | ACCESS, USAGE | https://datatopics.worldbank.org/g20fidata/ |
| G20 GPFI | ACCESS, USAGE, QUALITY | https://www.gpfi.org/data |

### Operator / agent network sources
| Source | Pillar focus | URL |
|---|---|---|
| Ethio Telecom / Telebirr | USAGE, QUALITY | https://www.ethiotelecom.et/telebirr-new/ |
| M-Pesa Ethiopia (Safaricom) | USAGE, ACCESS | https://m-pesa.safaricom.et/ |
| CBE Birr agent network | ACCESS (agents) | https://combanketh.et/ways-of-banking/network/cbebirr-agents |
| Dashen Bank agent list | ACCESS (agents) | https://dashenbanksc.com/wp-content/uploads/Total-number-of-Agent-list.pdf |
| Awash Bank agent list | ACCESS (agents) | https://www.awashbank.com/wp-content/uploads/2025/02/Agents-List-1.pdf |
| Anbesa Bank agent list | ACCESS (agents) | https://anbesabank.com/agent-list/ |
| Coop Bank Oromia agent list | ACCESS (agents) | https://coopbankoromia.com.et/wp-content/uploads/2022/11/COOPay-Ebirr-Agent-Web.xlsx |

### Analysis / secondary reporting (medium confidence, cross-check against a primary source where possible)
| Source | Pillar focus | URL |
|---|---|---|
| DFS Ethiopia Hub (Shega) | USAGE, QUALITY, ACCESS | https://digitalfinance.shega.co/ |
| Birr Metrics | ACCESS, GENDER, DEPTH | https://birrmetrics.com/ |
| UNCDF Ethiopia | QUALITY, ACCESS (agents) | https://www.uncdf.org/ |
| Center for Financial Inclusion | ACCESS, USAGE | https://www.centerforfinancialinclusion.org/technical-resources-and-data/ |

### Not yet found, worth targeted searching
- **TRUST pillar**: search NBE consumer protection directives, fraud/complaint statistics,
  or Findex's digital safety / password-protection module for Ethiopia specifically.
- **AFFORDABILITY**: search ITU's "cost of 2GB data as % of GNI per capita" for Ethiopia by year.
- **QUALITY**: search for network downtime/outage reports, or NBE dispute-resolution statistics.


## How to use this efficiently
1. Pick one source from the table.
2. Paste the source's URL or content into the prompt above.
3. Cross-check any returned indicator_code against the "already have" list before adding it avoid duplicates.
4. Append accepted rows to `data/processed/ethiopia_fi_unified_data_enriched.csv` (or `impact_links_enriched.csv`), and log them in `data_enrichment_log.md` using the same format as the existing entries.