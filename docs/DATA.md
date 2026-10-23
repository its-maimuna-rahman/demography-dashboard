# Data Sources and Calibration Documentation (`docs/DATA.md`)

This document records the empirical data sources, calibration methodologies, and sample benchmarks included in the **Vital Stats Suite**.

---

## 1. Primary Empirical Sources

### 1.1 Bangladesh Bureau of Statistics (BBS)
- **Population and Housing Census 2011 & 2022**:
  - National age-sex distributions (single-year and 5-year cohorts).
  - Marital status tables across reproductive and adult ages (used for Singulate Mean Age at Marriage / SMAM).
  - Post-Enumeration Check (PEC) net coverage omission rates (3.92% net undercount in 2011, 2.75% in 2022).
- **Report on Bangladesh Sample Vital Statistics (SVRS)** (Annual reports 1983–2023):
  - Age-Specific Fertility Rates (ASFR) and Total Fertility Rates (TFR).
  - Age-Specific Death Rates (ASDR), Infant Mortality Rate (IMR), Under-5 Mortality Rate (U5MR), Maternal Mortality Ratio (MMR).
  - Dual-record system based on the Chandra Sekar & Deming (1949) methodology for vital event completeness.
  - Internal and international migration modules.

### 1.2 Bangladesh Demographic and Health Survey (BDHS)
- Multi-round national survey data on fertility preferences, age at marriage, proximate determinants of fertility (contraceptive prevalence, infecundability), and child survival.

### 1.3 United Nations Population Division & WHO
- **UN World Population Prospects (WPP 2022/2024)**: Reference model fertility schedules and life tables for South Asia.
- **WHO Global Health Observatory**: World Standard Population (2000–2025) weights and reference Age-Specific Death Rates used for direct standardization (DSDR).

---

## 2. Bundled Datasets in `sample_data/`

All bundled datasets are deterministically regenerable via `python3 sample_data/generate_samples.py`:

| File | Type | Purpose | Mathematical Consistency Checks Passed |
|---|---|---|---|
| `census_2011.json` | JSON Baseline Benchmark | Represents the 2011 census baseline (~149.7M population, TFR 2.27, IMR 38.0). | Single-year sums equal 5-year sums ($<0.01\%$ diff). Infant + child deaths = 0–4 deaths. Male + Female = Total. |
| `census_2022.json` | JSON Modern Transition | Represents the 2022 census (~169.8M population, TFR 1.95, IMR 21.0). | Captures fertility decline and shifting dependency load. Tables reconciled. |
| `dirty_census.json` | JSON Stress Test | Historical census data with pronounced terminal digit preference on 0 and 5. | Used to test Whipple's Index, Myers' Blended Index, and missing data audits. |
| `time_series_1970_2024.csv` | CSV Time-Series | Longitudinal transition series from 1970 to 2024. | Calibrated against SVRS/UN WPP historical trajectories for Bangladesh. |

---

## 3. Data Integrity & Verification Standards

To prevent heuristic data invention:
1. **Zero Silent Inventions**: If marital status or dual-record fields are omitted, measures requiring them are reported as `unavailable` rather than synthesized.
2. **Exact Actuarial Conservation**: Single-year cohort interpolations via Sprague's osculatory graduation are prorated to match empirical 5-year group totals exactly.
3. **Dual Denominator / Numerator Adjustments**: Census coverage omission and death registration completeness are treated as distinct parameters (`(D / C_death) / (P / C_census)`).
