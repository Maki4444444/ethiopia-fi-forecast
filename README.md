# Ethiopia Financial Inclusion Forecasting

Data exploration, enrichment, and forecasting project analyzing financial inclusion trends in
Ethiopia (Access, Usage, Affordability, Gender, Quality, Trust, Depth), using a unified
event/observation/impact_link schema.

## Project Description

This project builds a forecasting pipeline for two of the seven financial-inclusion pillars, 
**Access** and **Usage**  by:
1. Exploring and enriching a starter dataset of survey observations, cataloged events (policy
   changes, product launches, market entries), and modeled event→indicator impact_links
2. Running exploratory analysis to surface patterns, gaps, and testable hypotheses
3. (Later tasks) Modeling event impacts and producing Access/Usage forecasts with an interactive
   dashboard

## Setup Instructions

```bash
# clone and enter the repo
git clone <repo-url>
cd ethiopia-fi-forecast

# create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS/WSL
# .\.venv\Scripts\Activate.ps1   # Windows PowerShell

# install dependencies
pip install -r requirements.txt

# launch notebooks
jupyter notebook notebooks/
```

## Data Sources

| Source | Used for |
|---|---|
| World Bank Global Findex (2011, 2014, 2017, 2021, 2025 waves) | Account ownership, savings, borrowing, gender splits |
| National Bank of Ethiopia (NBE) — Financial Stability Reports, draft NDPS 2.0 | Fraud losses, cyberattacks, national account activity |
| IMF Financial Access Survey (FAS) | Access indicators |
| ITU DataHub | Mobile data affordability |
| GSMA | Mobile money penetration |
| UNCDF Ethiopia | Agent network activity rates |
| Operator/press reporting (Shega, Birr Metrics, The Reporter Ethiopia, etc.) | Agent counts, product launches, incidents |

Every individual data point's exact source, quoted text, and confidence level is documented in
[`data_enrichment_log.md`](data_enrichment_log.md).

## The Unified Schema

All data lives in one table structure with a `record_type` column that determines which other
columns apply:

| `record_type` | What it represents | `category` | `pillar` |
|---|---|---|---|
| `observation` | A measured value from a survey/report/operator | empty | filled, dimension measured |
| `event` | Something that happened (policy, launch, milestone...) | filled,  event type | **empty (never pre-assigned)** |
| `impact_link` | A modeled estimate of an event's effect on an indicator | empty | filled, pillar of the affected indicator |
| `target` | An official policy goal | empty | filled, dimension of the goal |

**Key design rule:** events are never assigned a pillar directly, because a single event (e.g.
Telebirr's launch) can affect multiple pillars (Access *and* Usage) at once, pre-assigning one
pillar would bake a biased interpretation into supposedly neutral data. Instead, the *interpretation*
of which pillars an event affects lives only in separate `impact_link` rows, each pointing back at
its event via a `parent_id` column (like a foreign key).

Pillars: `ACCESS`, `USAGE`, `AFFORDABILITY`, `GENDER`, `QUALITY`, `TRUST`, `DEPTH`.

Valid values for every categorical column are enumerated in `data/raw/reference_codes.csv`.

## Repository Structure

```
ethiopia-fi-forecast/
├── .github/workflows/       # CI (unit tests on push/PR)
├── data/
│   ├── raw/                 # Original starter files, never edited in place
│   └── processed/           # Enriched dataset + impact_links (output of Task 1)
├── notebooks/
│   ├── 01_schema_understanding.ipynb   # Task 1: schema validation & exploration
│   └── 02_eda.ipynb                    # Task 2: exploratory data analysis
├── src/
│   ├── data_loader.py        # Load/validate the dataset, event-impact coverage checks
│   └── eda_utils.py          # Reusable analysis helpers used by the EDA notebook
├── dashboard/                # Streamlit app (later task)
├── models/                   # Trained/serialized models (later task)
├── reports/figures/          # Exported charts for the final report
├── tests/                    # pytest unit tests
├── data_enrichment_log.md    # Source/confidence documentation for every added record
├── enrichment_extraction_prompt.md   # Reusable prompt + source list for future enrichment
├── requirements.txt
└── README.md                 # this file
```

## Running the Analysis

```bash
# Task 1 schema validation and dataset exploration
jupyter nbconvert --to notebook --execute --inplace notebooks/01_schema_understanding.ipynb

# Task 2 exploratory data analysis
jupyter nbconvert --to notebook --execute --inplace notebooks/02_eda.ipynb

# run tests
pytest tests/ -v
```

## Current Status

- [x] Task 1: Data exploration and enrichment
- [x] Task 2: Exploratory data analysis
- [ ] Task 3: Event impact modeling
- [ ] Task 4: Forecasting
- [ ] Task 5: Dashboard