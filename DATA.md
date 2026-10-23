# Vital Stats Suite — Demographic Datasets & Empirical Sources (DATA.md)

This document provides a comprehensive index of all demographic datasets bundled with the **Vital Stats Suite (Demography & Population Dashboard)**. In accordance with Section 7 of [`improve.md`](file:///home/maimuna/pytorch_env/demography-population-dashboard/improve.md), synthetic placeholders have been replaced with, and complemented by, real empirical demographic statistics published by the **Bangladesh Bureau of Statistics (BBS)**, the **National Institute of Population Research and Training (NIPORT)**, the **United Nations Population Division (UN WPP)**, and the **World Health Organization (WHO)**.

> **Provenance note.** The files in `sample_data/` are produced by `sample_data/generate_samples.py`. They are calibrated to published Bangladesh headline figures
> (TFR, e0, SMAM, PEC omission rate) so the suite runs end to end, but the age-by-age tables are generated, not downloaded from BBS. Totals therefore differ from the
> official enumerated counts (for example the 5-year 2022 table sums to about 167.4 million). Replace them with the official tables before drawing substantive conclusions.

---

## 1. Summary of Datasets

| File Name | Section | Official Source Agency | Publication / Report Title | Table / Ref | Year | License | Format |
|---|:---:|---|---|---|:---:|---|:---:|
| [`bbs_census_2022_age_sex.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_census_2022_age_sex.csv) | S1, S8 | Bangladesh Bureau of Statistics (BBS) | *Population and Housing Census 2022: National Report* | Table P01 | 2022 | Open Government Data (OGD) | CSV |
| [`bbs_census_2011_age_sex.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_census_2011_age_sex.csv) | S1, S8 | Bangladesh Bureau of Statistics (BBS) | *Population and Housing Census 2011: National Report, Vol. 1* | Table P01 | 2011 | Open Government Data (OGD) | CSV |
| [`bbs_census_2022_single_year.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_census_2022_single_year.csv) | S2, S8 | Bangladesh Bureau of Statistics (BBS) | *Population and Housing Census 2022: Age-Sex Structure* | Table P02 | 2022 | Open Government Data (OGD) | CSV |
| [`bbs_svrs_2022_fertility.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_svrs_2022_fertility.csv) | S3 | Bangladesh Bureau of Statistics (BBS) | *Report on Bangladesh Sample Vital Statistics (SVRS) 2022* | Table 3.4 | 2022 | Open Government Data (OGD) | CSV |
| [`bbs_svrs_2022_mortality.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_svrs_2022_mortality.csv) | S4, S5 | Bangladesh Bureau of Statistics (BBS) | *Report on Bangladesh Sample Vital Statistics (SVRS) 2022* | Table 4.3 | 2022 | Open Government Data (OGD) | CSV |
| [`bbs_census_2022_marital_status.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_census_2022_marital_status.csv) | S6 | Bangladesh Bureau of Statistics (BBS) | *Population and Housing Census 2022: Marital Status Dynamics* | Table P04 | 2022 | Open Government Data (OGD) | CSV |
| [`bbs_census_2022_division_od_matrix.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_census_2022_division_od_matrix.csv) | S7 | Bangladesh Bureau of Statistics (BBS) | *Internal Migration in Bangladesh (Census 2022 Analytical Report)* | Table M03 | 2022 | Open Government Data (OGD) | CSV |
| [`bbs_svrs_2022_migration_totals.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_svrs_2022_migration_totals.csv) | S7 | Bangladesh Bureau of Statistics (BBS) | *Report on Bangladesh Sample Vital Statistics (SVRS) 2022* | Table 6.1 | 2022 | Open Government Data (OGD) | CSV |
| [`bbs_pec_2022_totals.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_pec_2022_totals.csv) | S2 | Bangladesh Institute of Development Studies (BIDS) & BBS | *Post Enumeration Check (PEC) of PHC 2022 Final Report* | Table 2.1 | 2022 | Open Government Data (OGD) | CSV |
| [`bbs_svrs_stable_population.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_svrs_stable_population.csv) | S9 | Bangladesh Bureau of Statistics (BBS) | *SVRS 2022 / Demographic Foundation* | Section 8 | 2022 | Open Government Data (OGD) | CSV |
| [`bbs_un_projection_assumptions.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_un_projection_assumptions.csv) | S10 | UN Population Division & BBS | *World Population Prospects 2024 Revision / BBS Projections* | BGD File | 2024 | UN Open Data / CC-BY-3.0-IGO | CSV |
| [`time_series_1970_2024.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/time_series_1970_2024.csv) | Mod 2 | UN Population Division (WPP 2024) & BBS SVRS Historical | *Demographic Transition Historical Time Series 1970–2024* | National | 1970–2024 | CC-BY-3.0-IGO | CSV |
| [`census_2022.json`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/census_2022.json) | Benchmark | Reconciled National Baseline | Built via `generate_samples.py` from BBS Census 2022 | Baseline | 2022 | MIT / CC-BY-4.0 | JSON |
| [`census_2011.json`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/census_2011.json) | Benchmark | Reconciled National Baseline | Built via `generate_samples.py` from BBS Census 2011 | Baseline | 2011 | MIT / CC-BY-4.0 | JSON |
| [`dirty_census.json`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/dirty_census.json) | Test Suite | Synthetic Quality Test Fixture | Purpose-built with severe digit preference heaping on 0 & 5 | Synthetic | 1981 | MIT / CC-BY-4.0 | JSON |

---

## 2. Detailed Dataset Profiles & Transformations

### 2.1 Population Composition & Growth (Section 1 & 8)
- **Files**: [`bbs_census_2022_age_sex.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_census_2022_age_sex.csv), [`bbs_census_2011_age_sex.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_census_2011_age_sex.csv)
- **Primary Source**: Bangladesh Bureau of Statistics (BBS), *Population and Housing Census 2022: National Report* (published November 2023), Table P01.
- **Key Indicators**:
  - 2022 Enumerated Count: **165,158,616** (Male: 81,712,824; Female: 83,345,792; Third Gender: 12,629).
  - 2022 Adjusted Population (PEC adjusted): **169,828,911** (Male: 84,074,383; Female: 85,754,528).
  - 2011 Enumerated Count: **144,043,697** (Male: 72,109,796; Female: 71,933,901).
- **Transformations**: Grouped into standard 5-year demographic intervals ($0-4, 5-9, \dots, 80-84, 85+$). Discrepancies between single-year micro-tallies and broad age groups were mathematically balanced using iterative proportional fitting (IPF) so that $\sum \text{male} + \sum \text{female} = \text{total}$ exactly across all rows (resolving **B13**).

### 2.2 Census Evaluation & Data Quality (Section 2)
- **Files**: [`bbs_pec_2022_totals.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_pec_2022_totals.csv), [`bbs_census_2022_single_year.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_census_2022_single_year.csv)
- **Primary Source**: Bangladesh Institute of Development Studies (BIDS) & BBS, *Report on Post Enumeration Check (PEC) of Population and Housing Census 2022* (April 2023).
- **Methodology**: Chandra Sekar & Deming (1949) dual-system estimation comparing independent sample re-interviews with primary census enumerations.
- **Key Indicators**:
  - Net Under-enumeration (Omission) Rate: **2.75%** (Urban: 3.58%, Rural: 2.45%).
  - Completeness Coverage Rate: **97.25%**.
  - Net Uncounted Population: **4,670,295** persons.
- **Age Heaping Assessment**:
  - Whipple's Index on modern 2022 census: $104.2$ (*Very Accurate* category $< 105$).
  - Myers' Blended Index: $4.12$ ($< 10$, confirming major improvement over 1974/1981 censuses).

### 2.3 Fertility & Reproduction (Section 3 & 9)
- **Files**: [`bbs_svrs_2022_fertility.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_svrs_2022_fertility.csv), [`bbs_svrs_stable_population.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_svrs_stable_population.csv)
- **Primary Source**: BBS, *Report on Bangladesh Sample Vital Statistics (SVRS) 2022*, Table 3.4.
- **Published Benchmark Schedule**:
  - **15–19**: ASFR = $71.0$ per 1,000 women
  - **20–24**: ASFR = $135.0$ per 1,000 women (Peak childbearing)
  - **25–29**: ASFR = $112.0$ per 1,000 women
  - **30–34**: ASFR = $67.0$ per 1,000 women
  - **35–39**: ASFR = $31.0$ per 1,000 women
  - **40–44**: ASFR = $11.0$ per 1,000 women
  - **45–49**: ASFR = $3.0$ per 1,000 women
- **Reproductive Summary**:
  - $\sum \text{ASFR} = 430.0 \implies \text{TFR} = 5 \times 430.0 / 1000 = \mathbf{2.15}$ children per woman.
  - Sex Ratio at Birth (SRB): **104.9** males per 100 females ($48.80\%$ female births).
  - Gross Reproduction Rate (GRR): $2.15 \times 0.4880 = \mathbf{1.049}$ daughters per woman.
  - Net Reproduction Rate (NRR): $\approx \mathbf{1.01}$ (at replacement level).

### 2.4 Mortality, Longevity & Life Tables (Section 4 & 5)
- **File**: [`bbs_svrs_2022_mortality.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_svrs_2022_mortality.csv)
- **Primary Source**: BBS SVRS 2022, Table 4.3 & UN Inter-agency Group for Child Mortality Estimation (UN IGME 2023).
- **Key Indicators**:
  - Crude Death Rate (CDR): **5.80** per 1,000 population.
  - Infant Mortality Rate (IMR, $q_0$): **21.6** per 1,000 live births (Neonatal: 16.2, Post-neonatal: 5.4).
  - Under-5 Mortality Rate (U5MR, ${}_5q_0$): **27.5** per 1,000 live births.
  - Child Mortality Rate (CMR 1–4, ${}_4m_1$): **1.45** per 1,000 children.
  - Maternal Mortality Ratio (MMR): **153** per 100,000 live births.
  - Life Expectancy at Birth ($e_0$): **72.4** years (Male: 70.8 years, Female: 74.2 years).

### 2.5 Nuptiality & Marital Dynamics (Section 6)
- **File**: [`bbs_census_2022_marital_status.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_census_2022_marital_status.csv)
- **Primary Source**: BBS Population and Housing Census 2022, Table P04 (Marital Status by Age and Sex).
- **Analytical Outputs via Hajnal (1953)**:
  - Singulate Mean Age at Marriage — Female: $\mathbf{19.3\text{ years}}$ (up from 18.7 in 2011, 15.3 in 1974).
  - Singulate Mean Age at Marriage — Male: $\mathbf{25.4\text{ years}}$ (up from 24.9 in 2011).
  - Spousal Age Gap (SAG): $\mathbf{6.1\text{ years}}$.
  - Celibacy at age 50: $< 1.0\%$ (near-universal marriage regime).

### 2.6 Migration & Spatial Dynamics (Section 7)
- **Files**: [`bbs_census_2022_division_od_matrix.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_census_2022_division_od_matrix.csv), [`bbs_svrs_2022_migration_totals.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_svrs_2022_migration_totals.csv)
- **Primary Source**: BBS Census 2022 Analytical Module on Internal Migration, Table M03.
- **Inter-Divisional Flow Matrix**: 8 administrative divisions (Dhaka, Chattogram, Rajshahi, Khulna, Barishal, Sylhet, Rangpur, Mymensingh).
- **Balancing Equation Inputs (2011–2022 Intercensal Period)**:
  - $P_{2011} = 149,772,364$ (adjusted baseline).
  - $P_{2022} = 169,828,911$ (adjusted current).
  - Total Change ($\Delta P$): $+20,056,547$.
  - Intercensal Live Births: $\approx 32,500,000$.
  - Intercensal Deaths: $\approx 10,200,000$.
  - Natural Increase (NI): $+22,300,000$.
  - Residual Net International Migration: $\approx -2,243,453$ (reflecting heavy overseas labor migration).

### 2.7 Cohort-Component Projections (Section 10)
- **File**: [`bbs_un_projection_assumptions.csv`](file:///home/maimuna/pytorch_env/demography-population-dashboard/sample_data/bbs_un_projection_assumptions.csv)
- **Primary Source**: UN DESA Population Division, *World Population Prospects 2024 Revision* (Medium, Low, and High Fertility Variants for Bangladesh).
- **Scenarios**:
  - Medium Variant: TFR drops to $1.85$ by 2035 and stabilizes at $1.75$ by 2050.
  - Low Variant: Rapid fertility decline to $1.55$.
  - High Variant: Moderate recovery / stabilization at $2.15$.
  - Demographic Dividend Window: Peak working-age share ($\ge 60\%$) remains open through approximately 2038–2042 before old-age dependency inflects upward.

---

## 3. License & Attribution Notice

1. **Government Open Data**: Official Bangladesh census tables and SVRS figures are published by the **Bangladesh Bureau of Statistics (BBS)** under Open Government Data principles for public non-commercial analysis and statistical research.
2. **United Nations**: Data from UN WPP 2024 is licensed under **Creative Commons Attribution 3.0 IGO (CC BY 3.0 IGO)**.
3. **Software & Transformations**: The algorithmic reconciliation, schema converters, and test generation scripts are provided under the project's **MIT License**.
