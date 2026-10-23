# CSV Schemas Reference Manual

This document defines the strict, authoritative schema specifications for all input CSV files accepted by the Vital Stats Suite across all syllabus sections (S1–S11).

## S1: Composition & Growth (`population_age_sex.csv`)

5-year or single-year age-sex population distribution.

| Column | Type | Required | Description | Example |
|---|---|---|---|---|
| `age_group` | `str` | Yes | Age group label (e.g. 0-4, 5-9, ..., 85+) | `0-4` |
| `male` | `float` | Yes | Male population count | `580000` |
| `female` | `float` | Yes | Female population count | `560000` |
| `total` | `float` | Optional | Total population count (optional, computed if missing) | `1140000` |

**Blank CSV Template:**
```csv
age_group,male,female,total
0-4,580000,560000,1140000
```

---

## S2: Data Quality (`pes_totals.csv`)

Post-Enumeration Check (PEC) or Dual-System coverage totals.

| Column | Type | Required | Description | Example |
|---|---|---|---|---|
| `indicator` | `str` | Yes | Coverage indicator name | `census_count` |
| `value` | `float` | Yes | Enumerated count or omission rate | `165158616` |

**Blank CSV Template:**
```csv
indicator,value
census_count,165158616
```

---

## S3: Fertility & Reproduction (`fertility_age.csv`)

Maternal 5-year age-specific fertility schedule (ages 15-49).

| Column | Type | Required | Description | Example |
|---|---|---|---|---|
| `age_group` | `str` | Yes | Maternal 5-year age group (15-19 ... 45-49) | `20-24` |
| `female_pop` | `float` | Yes | Number of women in age group | `6800000` |
| `births` | `float` | Yes | Total live births to women in age group | `918000` |
| `female_births` | `float` | Optional | Female births (optional, derived via SRB if omitted) | `447800` |
| `married_women` | `float` | Optional | Married women count (optional, unlocks marital rates) | `4760000` |
| `marital_births` | `float` | Optional | Marital live births (optional) | `872000` |

**Blank CSV Template:**
```csv
age_group,female_pop,births,female_births,married_women,marital_births
20-24,6800000,918000,447800,4760000,872000
```

---

## S4: Mortality & Standardization (`mortality_age_sex.csv`)

Age-specific deaths and mid-year population by age group.

| Column | Type | Required | Description | Example |
|---|---|---|---|---|
| `age_group` | `str` | Yes | Age group label (0-4, 5-9, ..., 85+) | `0-4` |
| `population` | `float` | Yes | Mid-year population in age bracket | `16200000` |
| `deaths` | `float` | Yes | Annual deaths in age bracket | `58320` |

**Blank CSV Template:**
```csv
age_group,population,deaths
0-4,16200000,58320
```

---

## S6: Nuptiality & Marital Dynamics (`marital_status.csv`)

Census counts by age group, sex, and marital status (for SMAM and celibacy).

| Column | Type | Required | Description | Example |
|---|---|---|---|---|
| `age_group` | `str` | Yes | Age bracket (15-19, 20-24, ..., 50-54) | `20-24` |
| `sex` | `str` | Yes | Sex ('male' or 'female') | `female` |
| `never_married` | `float` | Yes | Never-married (single) count | `3200000` |
| `married` | `float` | Yes | Currently married count | `4200000` |
| `widowed` | `float` | Optional | Widowed count | `45000` |
| `divorced` | `float` | Optional | Divorced count | `35000` |
| `separated` | `float` | Optional | Separated count | `12000` |

**Blank CSV Template:**
```csv
age_group,sex,never_married,married,widowed,divorced,separated
20-24,female,3200000,4200000,45000,35000,12000
```

---

## S7: Migration & Redistribution (`migration_totals.csv`)

Migration movements and demographic balancing equation components.

| Column | Type | Required | Description | Example |
|---|---|---|---|---|
| `indicator` | `str` | Yes | Indicator name (in_migrants, out_migrants, births, deaths) | `in_migrants` |
| `value` | `float` | Yes | Count or population parameter | `450000` |

**Blank CSV Template:**
```csv
indicator,value
in_migrants,450000
```

---

## S11: Population Projection (`projection_assumptions.csv`)

Assumptions for multi-cohort component population forecasting.

| Column | Type | Required | Description | Example |
|---|---|---|---|---|
| `indicator` | `str` | Yes | Assumption parameter key | `horizon_years` |
| `value` | `float` | Yes | Numeric parameter value | `30` |

**Blank CSV Template:**
```csv
indicator,value
horizon_years,30
```

---

