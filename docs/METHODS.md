# Vital Stats Suite — Authoritative Demographic Methods Manual (`docs/METHODS.md`)

This manual provides the complete mathematical formulations, demographic citations, standard quality scales, and plain-language interpretation guidelines for all measures implemented in the **Vital Stats Suite** across Syllabus Sections S1 through S11.

---

## 1. Syllabus Section S1: Composition & Growth

### 1.1 Masculinity Proportion (`MP`)
- **Full Form**: Masculinity Proportion
- **Formula**: $\text{MP} = \frac{P_m}{P_t} \times 100$
- **Citation**: Shryock, H. S., & Siegel, J. S. (1976). *The Methods and Materials of Demography*, Ch. 7.
- **Interpretation Rule**: "There are $X$ males and $100-X$ females per 100 people in the total population."

### 1.2 Sex Ratio (`SR`)
- **Full Form**: Sex Ratio
- **Formula**: $\text{SR} = \frac{P_m}{P_f} \times 100$
- **Citation**: United Nations Demographic Yearbook; Shryock & Siegel (1976).
- **Interpretation Rule**: "There are $X$ males for every 100 females in the population."

### 1.3 Sex Ratio at Birth (`SRB`)
- **Full Form**: Sex Ratio at Birth
- **Formula**: $\text{SRB} = \frac{B_m}{B_f} \times 100$
- **Citation**: Preston, S. H. et al. (2001). *Demography: Measuring and Modeling Population Processes*, Ch. 5.
- **Standard Range**: 103–107 male births per 100 female births (biological norm $\approx 105$).

### 1.4 Dependency Ratios (`TDR`, `CDR_CHILD`, `OADR`)
- **Total Dependency Ratio**: $\text{TDR} = \frac{P_{0-14} + P_{65+}}{P_{15-64}} \times 100$
- **Child Dependency Ratio**: $\text{CDR(Child)} = \frac{P_{0-14}}{P_{15-64}} \times 100$
- **Old-Age Dependency Ratio**: $\text{OADR} = \frac{P_{65+}}{P_{15-64}} \times 100$
- **Citation**: Bhende, A., & Kanitkar, T. (2010). *Principles of Population Studies*, Ch. 6.
- **Property**: $\text{TDR} = \text{CDR(Child)} + \text{OADR}$.

### 1.5 Child-Woman Ratio (`CWR`)
- **Formula**: $\text{CWR} = \frac{P_{0-4}}{W_{15-49}} \times 1,000$
- **Citation**: Newell, C. (1988). *Methods and Models in Demography*, Ch. 3.
- **Interpretation**: Index of fertility in settings where vital birth registration is incomplete.

### 1.6 Population Density & Growth Rates
- **Density**: $\text{Density} = \frac{\text{Population}}{\text{Area in km}^2}$
- **Exponential Growth Rate**: $r = \frac{\ln(P_2 / P_1)}{t}$
- **Doubling Time**: $T_d = \frac{\ln 2}{r}$
- **Natural Increase Rate**: $\text{NIR} = \frac{\text{CBR} - \text{CDR}}{10}$ (expressed in percent).

---

## 2. Syllabus Section S2: Data Quality & Evaluation

### 2.1 Whipple's Index (`WHIPPLE`)
- **Formula**: $W = \frac{\sum_{x=25,30,\dots,60} P_x}{\frac{1}{5} \sum_{y=23}^{62} P_y} \times 100$
- **Disaggregation**: Computed for Total, Males, and Females separately.
- **Scale**: $<105$ Highly accurate; $105-110$ Fairly accurate; $110-125$ Approximate; $125-175$ Rough; $\ge 175$ Very rough.
- **Citation**: United Nations (1955). *Manual II: Methods of Appraisal of Quality of Basic Data for Population Estimates*.

### 2.2 Myers' Blended Index (`MYERS`)
- **Formula**: $M = \frac{1}{2} \sum_{d=0}^9 |\%_d - 10.0\%|$ across blended populations over parameterized age bounds (default 10 to 69).
- **Scale**: $<5$ Low digit preference; $5-10$ Moderate; $10-20$ Substantial; $>20$ Severe age heaping.
- **Citation**: Myers, R. J. (1940). *Errors and Bias in the Reporting of Ages in Census Data*. TASA, 41: 395–415.

### 2.3 Post-Enumeration Check & Dual-System Estimation (`PEC`)
- **Formula**:
  $$N_{\text{true}} = \frac{N_{\text{census}} \times N_{\text{PES}}}{M_{\text{matched}}}$$
  $$\text{Completeness } C = \frac{M_{\text{matched}}}{N_{\text{PES}}}, \quad \text{Omission Rate } O = 1 - C$$
- **Citation**: Chandra Sekar, C., & Deming, W. E. (1949). *On a Method of Estimating Birth and Death Rates and the Extent of Registration*. JASA, 44(245): 101–115.

### 2.4 UN Age-Sex Accuracy Joint Score (`UN_JOINT_SCORE`)
- **Formula**: $\text{UN Index} = 3 \times \text{SRS} + \text{ARS}_{\text{male}} + \text{ARS}_{\text{female}}$
- **Scale**: $<20$ Accurate; $20-40$ Inaccurate; $>40$ Highly inaccurate.
- **Citation**: United Nations (1952). *Accuracy Tests for Census Age Distributions Tabulated in Five-Year and Ten-Year Groups*.

---

## 3. Syllabus Section S3: Fertility & Reproduction

### 3.1 Crude Birth Rate (`CBR`) & General Fertility Rate (`GFR`)
- $\text{CBR} = \frac{B}{P} \times 1,000$
- $\text{GFR} = \frac{B}{W_{15-49}} \times 1,000$

### 3.2 Age-Specific Fertility Rate (`ASFR`) & Total Fertility Rate (`TFR`)
- $\text{ASFR}_i = \frac{B_i}{W_i} \times 1,000$
- $\text{TFR} = 5 \times \sum_{i=1}^7 \frac{\text{ASFR}_i}{1,000}$
- **Citation**: Preston et al. (2001), Ch. 5.

### 3.3 Gross Reproduction Rate (`GRR`) & Net Reproduction Rate (`NRR`)
- $\text{GRR} = \text{TFR} \times \frac{B_f}{B}$
- $\text{NRR} = \sum_{i=1}^7 \text{ASFR}_{f,i} \times \frac{{}_5L_{x_i}}{l_0}$ (Exact life table person-years integration).
- **Criterion**: $\text{NRR} = 1.000$ represents exact generational demographic replacement.

### 3.4 General Marital Fertility Rate (`GMFR` / `MBR`)
- $\text{GMFR} = \frac{B_{\text{marital}}}{W_{\text{married}, 15-49}} \times 1,000$
- **Rule**: Explicitly requires empirical marital births; no silent synthetic replacement.

### 3.5 Bongaarts Proximate Determinants Framework
- $\text{TFR} = C_m \times C_c \times C_a \times C_i \times \text{TF}$
- **Total Fecundity (TF)**: Benchmark biological capacity $\approx 15.3$ births per woman.
- **Citation**: Bongaarts, J. (1978). *A Framework for Analyzing the Proximate Determinants of Fertility*. PDR, 4(1): 105–132.

---

## 4. Syllabus Section S4: Mortality & Standardization

### 4.1 Crude Death Rate (`CDR`) & Corrected CDR (`CORRECTED_CDR`)
- $\text{CDR} = \frac{D}{P} \times 1,000$
- **Dual Adjustment**: $\text{CDR}_{\text{corrected}} = \frac{D / C_{\text{death}}}{P / C_{\text{census}}} \times 1,000$
- **Rule**: Adjusts numerator by death registration completeness and denominator by census coverage; no fake defaults.

### 4.2 Infant & Child Mortality Series (`IMR`, `NMR`, `ENMR`, `PNMR`, `CMR(1-4)`, `U5MR`)
- **Infant Mortality Rate (IMR)**: $\frac{D_{<1\text{yr}}}{B} \times 1,000$
- **Neonatal Mortality Rate (NMR)**: $\frac{D_{<28\text{d}}}{B} \times 1,000$
- **Early Neonatal MR (ENMR)**: $\frac{D_{<7\text{d}}}{B} \times 1,000$
- **Post-Neonatal MR (PNMR)**: $\frac{D_{28\text{d}-1\text{yr}}}{B} \times 1,000$
- **Child Mortality Rate (CMR 1-4)**: $\frac{D_{1-4}}{P_{1-4}} \times 1,000$ (rate among children aged 1–4).
- **Under-5 Mortality Rate (U5MR)**: Derived from life table as $1,000 \times (1 - l_5 / l_0)$ or $\frac{D_{0-4}}{B} \times 1,000$.

### 4.3 Maternal Mortality Ratio (`MMR`)
- $\text{MMR} = \frac{\text{Maternal Deaths}}{B} \times 100,000$ live births.

### 4.4 Direct & Indirect Standardization (`DSDR`, `SMR`, `ISDR`)
- **Direct Standardized Death Rate (DSDR)**: $\sum (\text{ASDR}_i \times W^{\text{std}}_i) / \sum W^{\text{std}}_i$
- **Standardized Mortality Ratio (SMR)**: $\frac{D_{\text{observed}}}{\sum (P_i \times \text{ASDR}^{\text{std}}_i / 1,000)}$
- **Indirect Standardized Death Rate (ISDR)**: $\text{SMR} \times \text{CDR}^{\text{std}}$
- **Rule**: Strict standard rate requirement; never returns $1.000$ tautology when standards are absent.

---

## 5. Syllabus Section S5: Life Tables

### 5.1 Abridged & Complete Life Table Columns
- Exact age intervals $x$ to $x+n$:
  1. $n$: Interval length (1 for infant/complete, 4 for 1-4, 5 for 5-9...).
  2. ${}_n a_x$: Average person-years lived by those dying in interval (Chiang/Greville separation factor).
  3. ${}_n M_x$: Central death rate $= {}_n D_x / {}_n P_x$.
  4. ${}_n q_x$: Probability of dying $= \frac{n \times {}_n M_x}{1 + (n - {}_n a_x) \times {}_n M_x}$.
  5. ${}_n p_x$: Probability of surviving $= 1 - {}_n q_x$.
  6. $l_x$: Survivors at exact age $x$, starting with radix $l_0 = 100,000$.
  7. ${}_n d_x$: Deaths in interval $= l_x - l_{x+n}$.
  8. ${}_n L_x$: Person-years lived in interval $= n \times l_{x+n} + {}_n a_x \times {}_n d_x$.
  9. $T_x$: Cumulative person-years above age $x = \sum_{y \ge x} {}_n L_y$.
  10. $e_x$: Life expectancy at exact age $x = T_x / l_x$.
- **Citation**: Preston et al. (2001), Ch. 3; Chiang, C. L. (1984).

---

## 6. Syllabus Section S6: Nuptiality Dynamics

### 6.1 Singulate Mean Age at Marriage (`SMAM`)
- Calculates mean age at first marriage from proportions single ($S_x$):
  $$\text{SMAM} = \frac{15 + 5 \sum_{i=15-19}^{45-49} S_i - 50 \times S_{50}}{1 - S_{50}}$$
  where $S_{50} = \frac{S_{45-49} + S_{50-54}}{2}$.
- **Citation**: Hajnal, J. (1953). *Age at Marriage and Proportions Marrying*. Population Studies, 7(2): 111–136.

### 6.2 Marriage & Divorce Rates (`CMRG`, `CDVR`, `GDVR`)
- **Crude Marriage Rate (CMRG)**: $(M / P) \times 1,000$
- **Crude Divorce Rate (CDVR)**: $(\text{Div} / P) \times 1,000$
- **General Divorce Rate (GDVR)**: $(\text{Div} / P_{\text{married}}) \times 1,000$

---

## 7. Syllabus Section S7: Migration & Spatial Distribution

### 7.1 Migration Rates & Turnover
- **In-Migration Rate (IMR_M)**: $(I / P) \times 1,000$
- **Out-Migration Rate (OMR_M)**: $(O / P) \times 1,000$
- **Net Migration Rate (NMRG)**: $\frac{I - O}{P} \times 1,000$
- **Migration Efficiency Ratio (MER)**: $\frac{I - O}{I + O} \times 100$

### 7.2 Residual Balancing Equation
- $P_2 = P_1 + B - D + \text{NM} \implies \text{NM} = (P_2 - P_1) - (B - D)$
- **Citation**: United Nations (1970). *Manual VI: Methods of Measuring Internal Migration*.

---

## 8. Syllabus Section S8: Graduation & Age Smoothing

### 8.1 Sprague's Osculatory Interpolation
- Fifth-difference osculatory graduation converting 5-year cohorts $W_i$ into single-year estimates $g_x$.
- **Actuarial Re-Sum Property**: Every 5 single-year estimates are prorated to match the original 5-year group count exactly: $\sum_{x=0}^4 g_{5i+x} = W_i$.
- **Citation**: Sprague, T. B. (1880). *Explanation of a New Formula for Interpolation*. JIA; Shryock & Siegel (1976), Ch. 22.

---

## 9. Syllabus Section S9: Stable & Stationary Populations

### 9.1 Lotka's Intrinsic Equation
- Solves for intrinsic growth rate $r$ numerically:
  $$\sum_{i} e^{-r \cdot a_i} f_{f,i} \frac{{}_n L_{x_i}}{l_0} = 1$$
- **Intrinsic Birth Rate ($b$)**: $b = \left( \sum e^{-r \cdot a_i} \frac{{}_n L_{x_i}}{l_0} \right)^{-1}$
- **Intrinsic Death Rate ($d$)**: $d = b - r$
- **Stationary Population Equilibrium ($r=0$)**: $b = d = \frac{1}{e_0}$
- **Citation**: Lotka, A. J. (1907); Coale, A. J. (1972). *The Growth and Structure of Human Populations*.

---

## 10. Syllabus Section S10: Transition & Theory

### 10.1 Demographic Transition Stage Classifier
- Evaluates CBR, CDR, natural increase, TFR, and life expectancy to classify the demographic regime:
  - **Stage 1**: High Stationary (CBR $\ge 35$, CDR $\ge 30$).
  - **Stage 2**: Early Expanding (CBR high, CDR falling rapidly).
  - **Stage 3**: Late Expanding (CBR falling, CDR low).
  - **Stage 4**: Low Stationary (CBR and CDR low, TFR near replacement).
  - **Stage 5**: Natural Contracting (TFR $< 1.50$, deaths exceed births).

---

## 11. Syllabus Section S11: Cohort-Component Population Projection

### 11.1 Leslie / Life-Table Survival Forward Projection
- Forward shifts 5-year age-sex cohorts over $t \to t+5$:
  - Survived cohorts: $P_{x+5}(t+5) = P_x(t) \times \frac{{}_5 L_{x+5}}{{}_5 L_x} + \text{Net Migration}_x$
  - Open interval: $P_{85+}(t+5) = P_{80}(t) \times \frac{T_{85}}{T_{80}} + P_{85+}(t) \times \frac{T_{85}}{T_{85}}$
  - New births: $B = 5 \times \sum (W_i(t+2.5) \times \text{ASFR}_i)$
  - Infant cohort: $P_{0-4}(t+5) = B \times \frac{{}_5 L_0}{5 \times l_0}$
- **Scenarios**: Low, Medium, High fertility paths.
- **Dividend Window**: Identifies periods where working-age share (15–64) $\ge 60\%$ and dependency ratio $< 50$.
- **Citation**: Preston et al. (2001), Ch. 6; United Nations Population Division (2022).


---

## 12. Additional measures from the class revision sheet

Added to their existing sections. Formulas are shown as LaTeX on every measure card (see `engine/formulas.py`).

| Section | Measures |
|---|---|
| Composition | Percentage distribution (0-14, 15-64, 65+), percentage change, index of relative difference, index of dissimilarity, median-age classification |
| Fertility | Rate specific to order of birth, duration-specific marital fertility rate, age-adjusted birth rate (direct and indirect), proportion of births that are female, GRR shortcut (0.488 × TFR) |
| Mortality | Multi-year CDR (three versions), monthly, age-sex specific, cause-specific and endogenous/exogenous death rates, death ratio, cause-specific IMR, adjusted IMR (formulas A, B, C) with separation factor, perinatal, fetal and maternal rates |
| Life tables | Reed-Merrell person-years (L0, 4L1) and the handwritten L1, 3L2, 5L5 formulas (check these against your source) |
| Nuptiality | General, age-specific, first, second, age-order specific and total marriage rates, refined and duration-specific divorce rates, median age at first marriage (indirect) |
| Migration | In- and out-migration rates, gross and net migration, signed migration efficiency |
| Stable population | R1, R2, alpha, beta, quadratic approximation of r, T, mean age of childbearing (R1 / R0) |

Measures that need figures a census table does not hold (cause-specific deaths, fetal deaths, order-of-birth counts and so on) are calculators: enter the numbers and the result card appears. Nothing is guessed.
Median age at first marriage places each age group's proportion at the group mid-point and interpolates linearly; it is an approximation.
