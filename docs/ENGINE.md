# Vital Stats Suite — Core Demographic Engine Reference Manual (`ENGINE.md`)

> **Notice**: For the full, comprehensive mathematical reference covering all 11 syllabus sections (S1–S11), see [docs/METHODS.md](docs/METHODS.md).

This document summarizes the core mathematical, demographic, and statistical reference for the demographic measures and data quality checks implemented in the `engine/` package.

---

## 1. Data Quality Module (Section S2)

### 1.1 Whipple's Index ($W$)
Evaluates terminal digit preference for digits `0` and `5` in reported single-year age data in the adult range (ages 23 to 62 inclusive), disaggregated by Total, Male, and Female cohorts.

$$\text{Whipple's Index} = \frac{\sum_{x=25, 30, \dots, 60} P_x}{\frac{1}{5} \sum_{y=23}^{62} P_y} \times 100$$

- **Quality Scale**: $< 105$ (Highly accurate), $105 - 110$ (Fairly accurate), $110 - 125$ (Approximate), $125 - 175$ (Rough), $\ge 175$ (Very rough).
- **Citation**: United Nations (1955). *Manual II: Methods of Appraisal of Quality of Basic Data for Population Estimates*.

### 1.2 Myers' Blended Index ($M$)
Evaluates digit attraction across all 10 digits ($0, 1, \dots, 9$) over configurable age bounds (default 10 to 69).

$$M = \frac{1}{2} \sum_{d=0}^{9} \left| \%_d - 10.0\% \right|$$

- **Quality Scale**: $< 5$ (Low preference), $5-10$ (Moderate), $10-20$ (Substantial), $> 20$ (Severe age heaping).
- **Citation**: Myers, R. J. (1940). *Errors and Bias in the Reporting of Ages in Census Data*. TASA, 41: 395–415.

### 1.3 Post-Enumeration Check (PEC) & Dual-System Estimation
Evaluates under-enumeration and net coverage error via dual-system estimation:

$$N_{\text{true}} = \frac{N_{\text{census}} \times N_{\text{PEC}}}{M_{\text{matched}}}$$
$$\text{Omission Rate } (O) = \frac{N_{\text{true}} - N_{\text{census}}}{N_{\text{true}}}, \quad \text{Completeness } (C) = 1 - O$$

- **Citation**: Chandra Sekar, C., & Deming, W. E. (1949). *On a Method of Estimating Birth and Death Rates and the Extent of Registration*. JASA, 44(245): 101–115.

---

## 2. Master Syllabus Modules Summary

| Module | Title | Syllabus Coverage |
|---|---|---|
| **S1** | Composition & Growth | Masculinity Proportion (MP), Sex Ratio (SR), SRB, Age Dependency (TDR, CDR_child, OADR), Median Age, Child-Woman Ratio (CWR), Density, Growth Rates. |
| **S2** | Data Quality | Whipple's Index (Total, Male, Female), Myers' Blended Index, UN Joint Score, Age/Sex Ratio Scores, PEC Dual System Estimation. |
| **S3** | Fertility & Reproduction | CBR, GFR, ASFR Schedule, Total Fertility Rate (TFR), Gross Reproduction Rate (GRR), Net Reproduction Rate (NRR via life table), GMFR/MBR, Mean Age at Childbearing, Bongaarts Determinants. |
| **S4** | Mortality & Standardization | CDR, Corrected CDR (dual-adjustment), ASDR, Infant Mortality Series (IMR, NMR, ENMR, PNMR), CMR(1-4), U5MR, MMR, DSDR, SMR, ISDR. |
| **S5** | Life Tables | Complete and Abridged Life Tables ($x, n, nax, nMx, nqx, npx, lx, ndx, nLx, Tx, ex$), $e_0$, $e_{65}$, Adult Mortality ($45q15$). |
| **S6** | Nuptiality Dynamics | Singulate Mean Age at Marriage (SMAM by sex), Spousal Age Gap, Celibacy at 50, Crude Marriage Rate, Divorce Rates. |
| **S7** | Migration | In/Out/Net Migration Rates, Gross Migration Turnover, Migration Efficiency Ratio (MER), Residual Balancing Equation. |
| **S8** | Graduation & Smoothing | Sprague's Osculatory Interpolation (5-year $\to$ single-year with exact group re-sum conservation), Carrier-Farrag smoothing. |
| **S9** | Stable & Stationary Populations | Lotka's intrinsic growth rate ($r$) solver, Intrinsic Birth/Death Rates ($b, d$), Stationary Population ($b=d=1/e_0$). |
| **S10** | Transition & Theory | Demographic Transition Stage Classifier (Stages 1–5), Malthusian Subsistence demo. |
| **S11** | Population Projections | Leslie Matrix / Life-Table Survival Cohort-Component Projection (Low, Medium, High Scenarios), Dividend Window tracking. |

For detailed equations, worked examples, and full code mappings, consult [docs/METHODS.md](docs/METHODS.md).
