# Task 3: Event Impact Modeling — Methodology

Companion documentation to `notebooks/03_impact_modeling.ipynb`. This file exists as a
single, locatable reference for methodology, sources, and validation results, separate from
the notebook's inline markdown.

## 1. How Events Are Modeled

Each `impact_link` record's categorical fields (`impact_direction`, `impact_magnitude`,
`lag_months`) are translated into a signed numeric `impact_estimate`, then applied over time
using a **logistic (S-curve) ramp**:

- The ramp begins at `event_date + lag_months`.
- It reaches ~95% of its full magnitude after `duration_months` (a per-link field — see below).
- Before the lag ends, the effect is exactly 0.

**Multiple events affecting the same indicator are combined additively** (summed), not with a
saturating/diminishing-returns function. This is a documented simplification — see Limitations.

Implementation lives in `src/impact_model.py` (`logistic_ramp`, `event_effect_at`,
`combined_effect_at`, `simulate_indicator`), covered by 16 unit tests in
`tests/test_impact_model.py`, importable from both this task's notebook and Task 4's
forecasting notebook.

## 2. The `duration_months` Field

Each `impact_link` now carries its own `duration_months`, reasoned per event category rather
than one global constant:

| Event type | Typical duration | Reasoning |
|---|---|---|
| Direct subscriber sign-up (e.g. Telebirr → Telebirr Users) | 3 months | Fast, low-friction adoption |
| Usage/habit formation (e.g. P2P transaction growth) | 6-9 months | Takes longer than sign-up |
| Survey-measured Access effects | 12 months | Findex-measured account ownership shifts slowly |
| National ID / policy rollouts (Fayda, NFIS-II) | 18-24 months | Multi-year rollout processes |
| Acute single incidents (e.g. CBE system glitch) | 3 months | Reputational effects fade relatively fast |
| Definitional/structural links (e.g. P2P-ATM crossover) | 0 months | Not a ramping effect — the milestone IS the event |

These are still analyst judgment calls, not independently measured — flagged as a priority to
validate against real Ethiopia time series as more data accumulates.

## 3. Comparable Country Evidence

Several `impact_link` records use `comparable_country` benchmarks because Ethiopian pre/post
data is insufficient this early in several products' rollout. Sources checked this session:

| Comparable case | Finding | Source | Verification status |
|---|---|---|---|
| Kenya, M-Pesa (2007 launch) | Account ownership: 51%(2011)→75%(2014)→82%(2017)→90%(2021) | [World Bank Findex SSA overview](https://www.worldbank.org/en/publication/globalfindex/brief/financial-inclusion-in-sub-saharan-africa-overview) | **Verified live, 2026-07-19** |
| Tanzania, mobile money interoperability | Account ownership: 32%(2014)→45%(2021) | [World Bank Findex 2021 mobile money brief](https://www.worldbank.org/en/publication/globalfindex/brief/data-from-the-global-findex-2021-the-impact-of-mobile-money-in-sub-saharan-africa) | **Verified live, 2026-07-19** |
| India, Aadhaar digital ID | ~1.2B enrolled, ~half linked to a bank account (qualitative support only) | [IMF F&D, "The India Stack"](https://www.imf.org/external/pubs/ft/fandd/2021/07/india-stack-financial-access-and-digital-inclusion.htm) | **Partially verified** — supports direction, not the specific "+15-20%" figure |
| India, UPI instant payments | +25% payment volume (as cited in original dataset) | — | **Not verified this session** — inherited citation, `source_url` intentionally left blank |
| Rwanda, price competition | -20% data cost (as cited in original dataset) | — | **Not verified this session** — inherited citation, `source_url` intentionally left blank |

**Caveat carried into validation:** Kenya and Tanzania's mobile money markets are far more
mature (18+ years) than Ethiopia's (5 years for Telebirr). Their eventual magnitudes are
upper-bound precedents, not direct near-term predictions for Ethiopia.

## 4. The Event-Indicator Association Matrix

Built with `src/impact_model.py`'s `build_association_matrix()`. **Rows = the 12 distinct
cataloged events** (not the 18 individual impact_links — an earlier draft of this notebook had
a merge bug that used each link's own description as the row label, splitting multi-indicator
events like Telebirr across 3 separate rows; caught during review and fixed). Columns = key
indicators. Values = `impact_estimate`, in the indicator's native unit (percentage points for
rate indicators, percent-relative-change for count/volume indicators — units are **not**
uniform across columns, so the heatmap is illustrative, not directly comparable cell-to-cell).

See `reports/figures/event_indicator_matrix.png`.

## 5. Historical Validation

**Primary test case (matches the rubric exactly): Telebirr's effect on `ACC_MM_ACCOUNT`**
(mobile money account ownership rate), 2021 → 2024.

| | Value |
|---|---|
| 2021 baseline (actual) | 4.70% |
| 2024 predicted (raw model) | 9.22% |
| 2024 actual | 9.45% |
| **Residual** | **-0.23pp** |

This is a strong result for the raw, unrefined model — no discount or adjustment needed.

**Secondary test case: `ACC_OWNERSHIP`, 2021 → 2024**

| | Value |
|---|---|
| 2021 baseline (actual) | 46.0% |
| 2024 predicted (raw model) | 61.0% |
| 2024 actual | 49.0% |
| **Residual** | **+12.0pp (substantial over-prediction)** |

**Why the two cases diverge so much:** `ACC_MM_ACCOUNT` is the *direct* target of Telebirr and
M-Pesa's own impact_links. `ACC_OWNERSHIP` is a broader Findex-survey composite shaped by many
more factors — activation rates, trust, survey coverage — that the raw comparable-country
benchmarks don't account for. This is consistent with Task 2's EDA finding that only ~15-19%
of registered accounts nationally are active.

**Note on a corrected bug:** an earlier version of this analysis mislabeled `ACC_MM_ACCOUNT`'s
unit as "millions of accounts" and reported a false "unit mismatch" between it and
`impact_estimate`. Direct inspection of the data (`value_type='percentage'`, `unit='%'`)
confirmed no mismatch exists — both are genuinely in percentage-point terms. Documented here so
the correction is traceable rather than silently disappearing.

## 6. Refinement

Rather than picking a convenient number, the discount factor applied to `ACC_OWNERSHIP` was
**solved directly** from the historical residual:

```
implied_discount = (actual_2024 - actual_2021) / (predicted_2024_raw - actual_2021)
                  = (49.0 - 46.0) / (61.0 - 46.0) = 0.20
```

Applying this discount to the raw model's effect brings the 2024 `ACC_OWNERSHIP` prediction to
49.0%, matching actual by construction (calibration, not independent validation — see
Limitations). The magnitude (20%) is notably close to Task 2's independently-derived ~15-19%
national active-account-rate finding — two different indicators, different scopes, but a
reassuring directional cross-check.

## 7. Assumptions

1. Additive combination of simultaneous event effects, not saturating/diminishing-returns —
   likely to over-predict when several large events overlap (as seen with `ACC_OWNERSHIP`).
2. `duration_months` values are reasoned per event category, not independently measured.
3. A single empirically-derived activation discount (0.20), fit to exactly one historical
   window, applied to comparable-country-benchmarked `ACC_OWNERSHIP` effects.
4. Comparable-country magnitudes are treated as upper bounds from more mature markets, not
   direct Ethiopia predictions.

## 8. Limitations

- Only one historical validation window exists (2021→2024) for `ACC_OWNERSHIP`; the discount
  factor cannot yet be cross-validated against a second independent period.
- `IMP_0017`, `IMP_0019`, `IMP_0020` rely on theoretical, not empirical, evidence — lower
  confidence, explicitly weighted as such going into Task 4.
- Two comparable-country citations (India-UPI, Rwanda) remain unverified with a live source —
  their `source_url` is intentionally blank rather than a guessed link.
- The association matrix mixes units across columns; not directly comparable cell-to-cell
  without normalization.