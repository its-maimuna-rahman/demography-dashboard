# improve.md — Vital Stats Suite: what to fix, redesign and add

Written after reading every file you uploaded (engine, loader, quality, interpretation, reports, UI, app, tests, sample data, README, ENGINE.md, plan.md) and running the engine code to confirm the bugs marked **[run]**.

Files from the first upload batch (`base.py`, `pipeline.py`, `inference.py`, etc.) were no longer on disk when I ran things, so findings from those are marked **[read]**. I rebuilt a small `base.py` from your first upload to run the rest.

---

## 0. Short verdict

- The **formulas that are written are mostly right** (MP, SR, dependency ratios, CBR, GFR, ASFR, TFR, GRR, CDR, NMR, IMR, Whipple, direct standardization).
- The **pipeline around them is not trustworthy yet.** Several outputs look real but are made up or meaningless: SMR is always 1.000, NRR uses a hardcoded survival of 0.965, the CSV loader invents married-women and marital-birth numbers, and the sample data contradicts itself.
- For a serious project, fix correctness first, then restructure so each syllabus topic is its own section with its own CSV, then add the missing logic (life tables, nuptiality, migration, graduation, stable/stationary, proper projection).

Three parts, in the order you should do them:

| Part | What | Section |
|---|---|---|
| A | Bugs to fix | §1 |
| B | Things to redesign | §2 |
| C | Logic to add (your syllabus) | §3 to §6 |

---

## 1. Bugs to fix

### 1.1 Wrong or fake results (fix first)

| ID | Where | Problem | Fix |
|---|---|---|---|
| B1 **[run]** | `mortality.py` `calculate_smr_and_indirect_standardized_rate`, called from `compute_block_d` | The pipeline never passes standard rates, so the code falls into the `else` branch and computes expected deaths from the study population's own ASDRs. Result on census 2011 numbers: **SMR = 1.000000, ISDR = CDR = 8.1784**. It is a tautology shown as a finding. | Require real standard ASDRs (user-supplied, or a bundled reference such as a UN/WHO model schedule). If none, do not return SMR/ISDR. |
| B2 **[run]** | `mortality.py` `calculate_corrected_cdr`, fed by `pec_omission_rate` | Census undercount makes the **denominator too small**, so the true CDR is *lower* than raw. The code divides CDR by census completeness, so CDR goes **up** (8.178 → 8.449). It also mixes two different things: census coverage (PES) and death-registration completeness (dual record). Chandra Sekar–Deming and Bennett–Horiuchi are about *registration* completeness, not census PES. | Two separate inputs: `census_coverage` (adjust denominator: `P / C_census`) and `death_registration_completeness` (adjust numerator: `D / C_death`). Corrected CDR = `(D / C_death) / (P / C_census)`. |
| B3 **[run]** | same function | If no completeness is given it silently uses **0.95** and prints "adj. at 95.0% completeness" (8.42). | No defaults. If the input is missing, mark the measure unavailable. |
| B4 **[run]** | `mortality.py` `calculate_direct_standardized_rate` | If the age labels do not match the WHO standard (e.g. single-year labels "0","1",…), `fillna(0)` then an equal-weight fallback is used, but the output still says "WHO World Standard Population". Test result: **5.00**, which is just the mean of the rates. Same silent drop for unmatched groups such as "80+". | Regroup ages to the standard's groups, or raise an error. Never invent weights. Show which groups matched. |
| B5 **[run]** | `fertility.py` `calculate_net_reproduction_rate`, `compute_block_c` | `compute_block_c` never passes a life table, so NRR is always `GRR × 0.965` (confirmed: `method = approximate_survival`). | Build the female life table from the mortality schedule (see §4.2) and compute NRR from `nLx`. If no life table, label NRR "approximate" in the UI or hide it. |
| B6 **[run]** | `fertility.py` `compute_block_c` | If `marital_births` is missing, MBR silently uses **total** births but is still labelled marital (95.80 in my test). | Return unavailable. |
| B7 **[run]** | `loader.py` `_from_dataframe` | The CSV loader **invents data**: `married_women_15_49 = 65%` of women, `marital_births = 85%` of births, `year = 2024`, `female_births = births × 100/205`, `female_pop = total × 0.49` when sex is missing. Confirmed ratios 0.65 and 0.85 on the sample CSV. | Never invent. Leave `None`. If you want an assumption, make it an explicit user choice and record it in an `assumptions` field shown in the report. |
| B8 **[run]** | `quality.py` `calculate_myers_blended_index` | `start_age` / `end_age` are ignored. Score is 27.778 for both (10, 69) and (30, 40). | Use the parameters. Pick one age range, document it (textbook versions differ, commonly 10–89), and test against a worked example. |
| B9 **[read]** | `fertility.py` ASFR, `mortality.py` ASDR | The "measure" stores a scalar in `raw_value`: peak ASFR, and the **mean of ASDRs** (32.91 on census 2011). Then `interpret_measure` rates that scalar against bands (ASDR bands 5/10 per 1000), which means nothing. | Schedules should be DataFrames with summary stats (peak age, mean age at childbearing, etc.). Do not benchmark an average of age rates. |
| B10 **[run]** | `mortality.py` CMR | CMR is the 1–4 death rate when `child_deaths_1_4` and `pop_1_4` exist, but README/ENGINE.md call it U5MR, and `interpretation.py` rates it against the SDG U5MR target (≤25 per 1000 live births). Wrong unit for the benchmark. | Two measures: `CMR_1_4` (rate per 1000 children) and `U5MR` (from the life table, `1000 × (1 − l5/l0)`). |
| B11 **[read]** | `pipeline.py`, `quality.py`, README | `compute_block_a..d` can return **23** measures (3+4+7+9), but target is hardcoded 22. UI shows "23 / 22". `test_pipeline` asserts `>= 22` so it never fails. `run_all_quality_checks` divides by 22 and leaves out ISDR. | One registry of measures; compute counts from it. |
| B12 **[read]** | `quality.py` `validate_dataset_completeness` | Disagrees with what is computed: marks CORRECTED_CDR, NRR and SMR "computable" even though they use defaults or tautologies (B1, B3, B5). Block B uses a `(1, 1, 1)` placeholder hack. | Replace with schema-based "required fields" per measure (see §2). |

### 1.2 Data and sample files

| ID | Problem | Fix |
|---|---|---|
| B13 | `census_2011.json` (checked by hand): single-year ages sum to roughly **8.4M**, but `total_population` is 5.876M. Ages 65+ in the single-year table are about 2.3M vs `pop_65_plus` = 381k. 0–4 deaths in `mortality_schedule` (2,352) are **lower** than `infant_deaths + child_deaths_1_4` (2,634 + 1,008). Single-year populations barely fall with age (age 90 ≈ 83k vs age 0 ≈ 120k), so the pyramid is almost a rectangle. | Rebuild sample data so tables sum to the stated totals, or better, use real data (§7). Add a consistency check to the engine (§2, R4). |
| B14 | The JSON files do not match what `generate_samples.py` would produce, so the generator is not the source of truth. | One generator, one seed, outputs committed, test that regenerating gives the same files. |
| B15 | `time_series_1970_2024.csv` comes from `pct_elderly = 3.5 + 0.25·t·(1+0.02·t)`: by 2024 that is about **31.6% elderly and 48.8% working-age**. Not realistic, and unrelated to the census files (2022 file has 11% elderly). | Replace with real series (UN WPP / BBS) or clearly label "synthetic demo". |

### 1.3 Module 2 (`inference.py`) **[read]**

- Docstring says "cohort-component", but the code is **hand-set constants**: `young share = f(TFR × 7.5)`, `CDR = 4.5 + 0.32 × elderly share`, `CBR = TFR × 5.8 + …`. Nothing is calibrated, no age structure is simulated.
- Dividend-closure flag: `div_end` is the last year with working share ≥ 60%. If the share is still ≥ 60% at the final projected year, the code still raises "window closing". False alarm.
- Policy flags fire on fixed thresholds (OADR 25, TFR 1.5). Fine as a screen, but they are presented as recommendations. Need uncertainty and a "this is a screening rule" label.
- Module 2 always reads `time_series_1970_2024.csv`. It never uses the dataset you selected in Module 1.

### 1.4 Reports and app

| ID | Where | Problem | Fix |
|---|---|---|---|
| B16 | `pdf_export.py` | Dataset names and text go straight into ReportLab `Paragraph` markup. A name with `&` or `<` breaks the PDF. | Escape (`xml.sax.saxutils.escape`) every dynamic string. |
| B17 | `html_export.py` | Escapes some fields, not `m.name`, `m.formula`, `m.code`, `q.status`. Imports `ui.components`, which imports **Streamlit**, so "standalone export" needs Streamlit. `app.py` never passes `pyramid_html_div`, so the exported dashboard has **no pyramid**, yet README calls it "interactive". | Escape everything. Move gauge HTML into `reports/` with no UI import. Embed charts (static SVG or inline Plotly) or stop calling it interactive. |
| B18 | `app.py` | PDF ×2 and HTML are **built on every Streamlit rerun**, even if nobody clicks download. Pipeline and comparison are not cached. `explain_missing_gap` runs per gap per rerun, with a 4 s Gemini timeout each. | `st.cache_data` for pipeline results. Build exports only on button click. Make LLM explanations a button. |
| B19 | `missing_assistant.py` | API key placed in the URL query string. | Send in the `x-goog-api-key` header. Better: make this feature optional and off by default (§2, R10). |
| B20 | `fertility.py` | `Union` is used but not imported. Works only because of `from __future__ import annotations`. | Import it. Add `mypy` to CI. |
| B21 | `quality.py` | Whipple: an incomplete 23–62 range hits a bare `pass` and is computed anyway. Only total, no by-sex. Recommendations name Feeney / Carrier–Farrag smoothing that does not exist in the engine. | Fail or warn on gaps. Compute by sex. Add the graduation module (§5.8). |
| B22 | `quality.py`, `ENGINE.md` | Citation: the dual-record paper is **Chandra Sekar, C. & Deming, W. E. (1949)**, JASA 44(245):101–115. "Chandrasekaran" is the wrong surname form. PEC is net only (no gross omission / erroneous inclusion, no by-age-sex coverage). | Fix citation. Extend PES (§5.2). |
| B23 | `interpretation.py` | Labels like "EXCELLENT" for CBR 16–25 or TFR 1.8–2.2 are value judgments. Fertility and sex ratio are not good or bad. CDR bands ignore age structure. | Use neutral regime labels for demographic-regime measures (TFR, CBR, ACR, SR). Keep good/bad ratings for health outcomes (IMR, NMR, U5MR, MMR). Mark every band as sourced or heuristic, with the source. |

### 1.5 Tests are too weak to catch any of the above

`>= 22`, `> 0.95`, `status in (...)`. None of B1 to B12 would fail a test. Add regression tests:

- `SMR` with no standard supplied → measure absent (not 1.0).
- Census coverage 96.8% and no death-registration input → corrected CDR absent, plain CDR lower than raw when only denominator is adjusted.
- Loader on the sample CSV → `married_women_15_49 is None`.
- Myers: different `start_age/end_age` → different scores.
- Single-year labels with `DSDR` → either regrouped result or `ValueError`.
- Sample JSON: table totals equal stated totals within 0.5%.

---

## 2. What to redesign

Plain list, each one short. Do R1 to R4 together.

**R1. One section = one self-contained module.**
Your syllabus is already sectioned (fertility, mortality, nuptiality, migration, graduation, stable). Make the code match:

```
vitalstats/
  core/          result types, units, registry, errors, benchmark loader
  io/            schemas (one per section), readers, template generator, validators
  sections/
    composition/   age-sex structure, ratios, growth, density
    quality/       Whipple, Myers, UN joint score, PES, registration completeness
    fertility/
    mortality/
    lifetable/     complete, abridged, multiple decrement, working life, model tables
    nuptiality/
    migration/
    graduation/
    stable/        stable and stationary populations
    transition/    transition stage classifier, Malthus demo
    projection/    cohort-component projection (replaces inference.py)
  reports/       shared templates + one builder per section
  ui/            one Streamlit page per section
data/templates/  one blank CSV per input file
data/samples/    committed, regenerable
tests/           one folder per section
docs/            METHODS.md (replaces ENGINE.md), DATA.md
```

**R2. Stop guessing CSV shapes.**
`loader._from_dataframe` guesses between key-value, wide, and age-sex tables with heuristics. Replace with **one explicit schema per file** (§4). Each schema is a small spec: columns, type, required/optional, allowed values, checks. From that one spec generate: the blank CSV template, the validator, the on-screen help, and the docs table. Single source of truth.

**R3. Break up the 50-field `DemographicDataset`.**
Use typed inputs per section: `PopulationInput`, `FertilityInput`, `MortalityInput`, `NuptialityInput`, `MigrationInput`, `ProjectionInput`. A section only sees its own data.

**R4. Better result object and cross-table consistency checks.**
Add to the result: `status` (`computed` / `approximate` / `unavailable`), `method`, `assumptions`, `warnings`, optional `ci`. Add a validation layer before any calculation:

- stated total vs table sums (population, births, deaths)
- births vs ASFR sums
- infant + child deaths ≤ 0–4 deaths
- no negative counts, no age gaps, no duplicate age groups
- male + female = total where total is given

**R5. Separate calculation from interpretation.**
`interpretation.py` bands should live in a data file (`benchmarks.yaml`) with `source`, `year`, `is_heuristic` per band. Calculations never import it.

**R6. UI: multi-page and cached.**
`st.navigation` with one page per section. Each page: download template → upload CSV → validation messages → results → export. Cache pipeline results. Build exports on click only.

**R7. Reports.**
Per-section PDF and HTML from shared templates (Jinja2). Remove any UI import from `reports/`. Include assumptions and warnings in every report.

**R8. Module 2 becomes the projection section.**
Input: base age-sex population + ASFR + life table (or survival ratios) + sex ratio at birth + net migration by age. Output: cohort-component projection with low/medium/high scenarios. It should be fed by the other sections, not a fixed CSV.

**R9. Packaging and CI.**
`pyproject.toml`, `src/` layout, GitHub Actions running `pytest`, `ruff`, `mypy`. Replace `python3 app.py` launcher hack with `streamlit run`.

**R10. LLM assistant: optional, off by default.**
Keep the deterministic missing-column text. The Gemini call adds a network dependency and a key to leak. If you keep it, use a header for the key, and trigger it by button.

**R11. Housekeeping.**
Remove "Claude-pilled" and "Google Antigravity" from README and HTML footer. Remove the absolute `file:///home/maimuna/...` link. Rename `plan.md` to `docs/HISTORY.md` or delete it. Update ENGINE.md counts (see B11).

---

## 3. Sections and what each one computes (broad view first)

Your syllabus screenshot, mapped to sections. **Priority** is my suggestion; reorder freely.

| # | Section | Syllabus topic | Priority | Status today |
|---|---|---|---|---|
| S1 | Composition & growth | commonly used ratios: sex ratio, child-woman ratio, dependency ratio, density | High | partial (A, B blocks) |
| S2 | Data quality | errors in demographic data, testing accuracy, PEC, adjustment | High | partial (Whipple, Myers, PEC) |
| S3 | Fertility | fertility measures, fecundity vs fertility, trends | High | partial (Block C) |
| S4 | Mortality | mortality measures, standardization, trends | High | partial (Block D) |
| S5 | Life tables | complete / abridged, multiple decrement, working life, model tables | **High (missing, core)** | none |
| S6 | Nuptiality | marriage, age at marriage, celibacy, widowhood, divorce, separation, effect on fertility | **High (missing)** | none |
| S7 | Migration | internal / international, sources, measures, impact | **High (missing)** | none |
| S8 | Graduation | graduation of age distribution | Medium (missing) | none |
| S9 | Stable & stationary | stable and stationary populations | Medium (missing) | none |
| S10 | Transition & theory | demographic transition, Malthus | Low (explanatory) | none |
| S11 | Projection | future trajectory | Medium | weak (`inference.py`) |

Your note says the syllabus screenshot has no measurement statistics (general divorce rate, total divorce rate, etc.). §5 fills that in from standard demography texts and my web search. Every formula is listed so you can check it against your course book before coding.

---

## 4. Input CSV shapes per section

Rules for all files:

- UTF-8, header row, `snake_case` column names, one table per file, no merged cells.
- Age labels: `0-4, 5-9, …, 80-84, 85+` for grouped; integers `0, 1, …` for single-year. Open interval last.
- Sex values: `male`, `female`, `both`.
- Counts are integers ≥ 0. Rates are never inputs (the engine computes them).
- Every file may carry optional `year` and `region` columns. If absent, the user sets them in the UI.
- Key-value files use `indicator,value`.

Each row below is a file the UI should offer as a blank template.

### S1 Composition & growth

| File | Columns | Notes |
|---|---|---|
| `population_age_sex.csv` | `age_group` (or `age`), `male`, `female` | `total` optional (computed). |
| `population_totals.csv` | `indicator,value` | `area_km2`, `urban_population`, `year`. |
| `population_series.csv` | `year`, `population` | Two or more censuses; for growth rates and doubling time. |

### S2 Data quality

| File | Columns | Notes |
|---|---|---|
| `population_age_sex.csv` | single-year `age`, `male`, `female` | Needed for Whipple, Myers. 5-year is enough for age-ratio / sex-ratio scores. |
| `pes_totals.csv` | `indicator,value` | `census_count`, `pes_count`, `matched_count`; optional `erroneous_inclusions`. |
| `pes_age_sex.csv` | `age_group`, `sex`, `census_count`, `pes_count`, `matched_count` | Optional: coverage by age and sex. |
| `dual_record.csv` | `event`, `system_a_count`, `system_b_count`, `matched_count` | Registration completeness (births, deaths). `event` in `birth`, `death`. |

### S3 Fertility

| File | Columns | Notes |
|---|---|---|
| `fertility_age.csv` | `age_group`, `women`, `births` | Required. 15-19 … 45-49. |
| | + optional `female_births`, `married_women`, `marital_births`, `children_ever_born` | Each optional column unlocks more measures (GRR by daughters, marital rates, parity). |
| `fertility_totals.csv` | `indicator,value` | `live_births`, `male_births`, `female_births`, `midyear_population`, `children_0_4`, `women_15_49`. |
| `parity.csv` | `age_group`, `parity`, `women` | Optional: parity progression ratios. |

### S4 Mortality

| File | Columns | Notes |
|---|---|---|
| `mortality_age_sex.csv` | `age_group`, `sex`, `population`, `deaths` | Long format, by sex. Required for ASDR and standardization. |
| `vital_events.csv` | `indicator,value` | `live_births`, `deaths_total`, `neonatal_deaths`, `early_neonatal_deaths`, `infant_deaths`, `deaths_1_4`, `stillbirths`, `maternal_deaths`, `midyear_population`, `women_15_49`. |
| `deaths_by_cause.csv` | `cause`, `age_group`, `sex`, `deaths` | Optional: cause-specific and proportional mortality. |
| `standard_population.csv` | `age_group`, `weight` | Optional. Default: WHO 2000–2025. |
| `standard_rates.csv` | `age_group`, `asdr_per_1000` | Optional. Needed for indirect standardization / SMR. |
| `registration_completeness.csv` | `indicator,value` | `death_completeness`, `census_coverage` (kept apart, see B2). |

### S5 Life tables

| File | Columns | Notes |
|---|---|---|
| `mortality_age_sex.csv` | as S4 | Builds abridged tables (5-year groups + 0, 1-4) or complete tables (single year). |
| `lifetable_given.csv` | `age`, `lx` | Optional: start from a published `lx` column. |
| `multiple_decrement.csv` | `age_group`, `population`, `deaths_cause_a`, `deaths_cause_b`, … | Competing causes. |
| `working_life.csv` | `age_group`, `participation_rate` | With a life table gives working life expectancy. |

### S6 Nuptiality

| File | Columns | Notes |
|---|---|---|
| `marital_status.csv` | `age_group`, `sex`, `never_married`, `married`, `widowed`, `divorced`, `separated` | Census counts. Required for SMAM, % never married, celibacy, widowhood. `separated` optional (your syllabus lists it). |
| `marriages.csv` | `age_group`, `sex`, `marriages`, `first_marriages` | Registration or survey. `first_marriages` optional. |
| `divorces.csv` | `age_group`, `sex`, `divorces`, `married_population` | Age-specific divorce rates. |
| `divorces_duration.csv` | `marriage_duration`, `divorces`, `marriages_cohort` | Optional: duration-specific, total divorce rate. |
| `nuptiality_totals.csv` | `indicator,value` | `marriages`, `divorces`, `midyear_population`, `population_15_plus`, `married_women_15_49`. |

### S7 Migration

| File | Columns | Notes |
|---|---|---|
| `migration_totals.csv` | `indicator,value` | `population_start`, `population_end`, `births`, `deaths`, `in_migrants`, `out_migrants`, `period_years`. Any missing term gets estimated by the balancing equation. |
| `region_migration.csv` | `region`, `population_t1`, `population_t2`, `in_migrants`, `out_migrants`, `area_km2` | Rates per region, index of redistribution. |
| `migration_flows.csv` | `origin`, `destination`, `migrants` | Origin–destination matrix, streams and counter-streams. |
| `census_pair_age.csv` | `age_group`, `population_t1`, `population_t2` | Census survival ratio method. Needs a life table for the life-table survival ratio method. |
| `birthplace.csv` | `birthplace`, `residence`, `persons` | Lifetime migration. |
| `migrants_age.csv` | `age_group`, `sex`, `in_migrants`, `out_migrants`, `population` | Age-specific rates. |

### S8 Graduation

Uses `population_age_sex.csv` (single-year or 5-year). Options set in the UI: method, target (single year or smoothed groups).

### S9 Stable & stationary

Uses the female life table from S5 and `fertility_age.csv` (daughters). Option: `observed_growth_rate`.

### S11 Projection

| File | Columns | Notes |
|---|---|---|
| `population_age_sex.csv` | as S1 | Base year. |
| `fertility_age.csv` | as S3 | Base ASFR. |
| `mortality_age_sex.csv` | as S4 | Builds survival ratios. |
| `projection_assumptions.csv` | `indicator,value` | `base_year`, `horizon_years`, `srb` (default 105 male per 100 female, editable), `tfr_target_low/medium/high`, `e0_gain_per_year`. |
| `net_migration_age_sex.csv` | `age_group`, `sex`, `net_migrants_per_year` | Optional. Default 0 and the report says "closed population". |

### Validation messages

Every error names the file, row and column: `mortality_age_sex.csv, row 14: deaths = -3 (must be ≥ 0)`. Missing optional columns produce a note, not an error: `children_ever_born not provided → parity measures unavailable`.

---

## 5. Statistics catalogue

Every measure I would put in the engine, grouped by section. Notation: `P` mid-year population, `B` live births, `D` deaths, `n` age interval, `x` exact age, `nMx` death rate, `nqx` probability of dying, `lx` survivors, `nLx` person-years, `Tx` total person-years above x, `ex` life expectancy.

Legend:
- ✔ = standard formula, I am confident in it.
- ◇ = confirm the exact form in your textbook before coding (several versions exist, or I could not verify the constants).
- **New** = not in the project today.

### 5.1 S1 Composition & growth

| Measure | Formula | Status |
|---|---|---|
| Masculinity proportion | `M / (M+F) × 100` ✔ | exists |
| Sex ratio (total, by age group) | `M / F × 100` ✔ | exists (total only) |
| Sex ratio at birth | `male births / female births × 100` ✔ | **New** |
| Excess of males | `M − F` ✔ | exists |
| Age composition ratios | `P_group / P × 100` ✔ | exists |
| Total / child / old-age dependency ratio | `(P0-14 + P65+) / P15-64 × 100`, etc. ✔ | exists |
| Ageing index | `P65+ / P0-14 × 100` ✔ | **New** |
| Potential support ratio | `P15-64 / P65+` ✔ | **New** |
| Median age | interpolate cumulative distribution to 50% ✔ | **New** |
| Child-woman ratio | `P0-4 / W15-49 × 1000` ✔ | **New** (in your syllabus) |
| Sundbarg type | compare `0-14 : 15-49 : 50+` shares → progressive / stationary / regressive ◇ | **New** |
| Population density | `P / area_km2` ✔ | **New** (in your syllabus) |
| Urbanization level | `urban / P × 100` ✔ | **New** |
| Arithmetic growth rate | `(P2 − P1) / (P1 × t)` ✔ | **New** |
| Geometric growth rate | `(P2 / P1)^(1/t) − 1` ✔ | **New** |
| Exponential growth rate | `ln(P2 / P1) / t` ✔ | **New** |
| Doubling time | `ln 2 / r_exp` ✔ | **New** |
| Natural increase rate | `CBR − CDR` (per 1000) ✔ | **New** |
| Vital index | `B / D × 100` ✔ | **New** |
| Population change equation | `P2 = P1 + B − D + I − O` ✔ | **New** |

### 5.2 S2 Data quality

| Measure | Formula | Status |
|---|---|---|
| Whipple's index | digits 0 and 5, ages 23–62 ✔ | exists (by total only) |
| Myers' blended index | see B8 ◇ | exists, bug |
| Digit-specific indices (Noumbissi) | digit preference for each digit ◇ | **New** |
| Bachi index ◇ | | **New** |
| Age ratio score | `ARS_i = abs(200 × P_i / (P_{i−1} + P_{i+1}) − 100)` ✔ | **New** |
| Sex ratio score | mean absolute successive difference of age-group sex ratios ✔ | **New** |
| UN age-sex accuracy (joint) index | `3 × SRS + ARS_male + ARS_female` ✔ | **New** |
| Sex ratio at birth check | compare to ~105 (plausible band about 103–107) ✔ | **New** |
| PES / dual-system estimate | `N = C × P / M`; completeness `= M / P`; net undercount `= (N − C) / N` ✔ | exists (net only) |
| Gross omission, erroneous inclusion | from matched and unmatched counts in the PES ◇ | **New** |
| Coverage by age and sex | PES by age-sex group ✔ | **New** |
| Registration completeness (dual record) | `N = n1 × n2 / m`; completeness of system 1 `= m / n2` ✔ | **New** |
| Growth balance / generalized growth balance, Brass methods ◇ | | **New (advanced)** |
| Demographic analysis (expected vs enumerated cohort) ◇ | | **New (advanced)** |

### 5.3 S3 Fertility

| Measure | Formula | Status |
|---|---|---|
| Crude birth rate | `B / P × 1000` ✔ | exists |
| General fertility rate | `B / W15-49 × 1000` ✔ | exists |
| ASFR | `B_i / W_i × 1000` ✔ | exists |
| Total fertility rate | `n × Σ ASFR_i / 1000` ✔ | exists |
| Gross reproduction rate | `TFR × (B_f / B)` or `n × Σ ASFR_female_i / 1000` ✔ | exists |
| Net reproduction rate | `Σ ASFR_female_i × nL_i / l0` (per-woman rates) ✔ | exists, fake survival (B5) |
| General marital fertility rate | `B_marital / married women 15-49 × 1000` ✔ | exists (bug B6) |
| Age-specific marital fertility rate | `B_marital_i / married women_i` ✔ | **New** |
| Total marital fertility rate | `n × Σ ASMFR_i` ✔ | **New** |
| Mean age at childbearing | `Σ (x_i + n/2) × ASFR_i / Σ ASFR_i` ✔ | **New** |
| Child-woman ratio | see S1 ✔ | **New** |
| Sex ratio at birth | see S1 ✔ | **New** |
| Mean children ever born (parity) | `Σ children / women` by age group ✔ | **New** |
| Parity progression ratio | `a_i = P_{i+1} / P_i` (women of parity ≥ i+1 over ≥ i) ✔ | **New** |
| Completed cohort fertility | sum of cohort ASFRs over a cohort's life ✔ | **New** |
| Mean generation length | `T ≈ ln(NRR) / r` ✔ | **New** |
| Intrinsic growth rate (approx) | `r ≈ ln(NRR) / T` ✔ | **New** |
| Coale's Princeton indices `If, Ig, Im, Ih` | observed births / births under Hutterite fertility ◇ | **New (advanced)** |
| Bongaarts proximate determinants | `TFR = Cm × Cc × Ca × Ci × TF` with TF ≈ 15.3 ✔; `Cm = TFR / TMFR` style index ◇ | **New (advanced)** |
| Brass P/F ratio (fertility correction) ◇ | | **New (advanced)** |
| Rele's method (TFR from child-woman ratio) ◇ | | **New (advanced)** |

Your syllabus lists "fecundity and its relationship with fertility". That is conceptual (fecundity = biological capacity, fertility = actual births). A short explanatory card plus the Bongaarts model is the quantitative link.

### 5.4 S4 Mortality

| Measure | Formula | Status |
|---|---|---|
| Crude death rate | `D / P × 1000` ✔ | exists |
| Corrected CDR | see B2 ✔ | exists, wrong |
| ASDR (age-sex specific) | `D_i / P_i × 1000` ✔ | exists (total only; add by sex) |
| Infant mortality rate | `infant deaths / B × 1000` ✔ | exists |
| Neonatal MR | `deaths < 28 d / B × 1000` ✔ | exists |
| Early neonatal MR | `deaths < 7 d / B × 1000` ✔ | **New** |
| Post-neonatal MR | `(infant − neonatal deaths) / B × 1000` ✔ | **New** |
| Child death rate 1–4 | `D1-4 / P1-4 × 1000` ✔ | exists (renamed, B10) |
| Under-5 mortality rate | `1000 × (1 − l5 / l0)` from life table ✔ | **New** |
| Stillbirth rate | `late fetal deaths / (B + late fetal deaths) × 1000` ✔ | **New** |
| Perinatal mortality rate | `(late fetal deaths + early neonatal deaths) / (B + late fetal deaths) × 1000` ✔ | **New** |
| Maternal mortality ratio | `maternal deaths / B × 100,000` ✔ | **New** |
| Maternal mortality rate | `maternal deaths / W15-49 × 100,000` ✔ | **New** |
| Lifetime risk of maternal death | `1 − (1 − MMR/100,000)^TFR` ✔ | **New** |
| Cause-specific death rate | `deaths_cause / P × 100,000` ✔ | **New** |
| Proportional mortality | `deaths_cause / total deaths × 100` ✔ | **New** |
| Case fatality rate | `deaths from disease / cases × 100` ✔ | **New** |
| Adult mortality `45q15` | `1 − l60 / l15` ✔ | **New** |
| Sex differential in mortality | sex ratio of deaths; `e0` gap ✔ | **New** |
| Direct standardized rate | `Σ ASDR_i × W_i / Σ W_i` ✔ | exists (bug B4) |
| Indirect standardization: expected deaths, SMR, ISDR | `E = Σ P_i × ASDR_std_i`; `SMR = D / E`; `ISDR = SMR × CDR_std` ✔ | exists (bug B1) |
| Comparative mortality figure ◇ | | **New** |
| Kitagawa decomposition | `R1 − R2 = Σ (c1_i − c2_i)(r1_i + r2_i)/2 + Σ (r1_i − r2_i)(c1_i + c2_i)/2` ✔ | **New** |

### 5.5 S5 Life tables

Columns: `x, n, nax, nMx, nqx, npx, lx, ndx, nLx, Tx, ex`.

| Step / measure | Formula | Status |
|---|---|---|
| Death rate | `nMx = nDx / nKx` ✔ | **New** |
| Probability of dying | `nqx = n × nMx / (1 + (n − nax) × nMx)` ✔ | **New** |
| Survivors, deaths | `l(x+n) = lx × (1 − nqx)`; `ndx = lx − l(x+n)` ✔ | **New** |
| Person-years lived | `nLx = n × l(x+n) + nax × ndx` ✔ | **New** |
| Open interval | `q = 1`, `L = l / M` ✔ | **New** |
| Total person-years, life expectancy | `Tx = Σ_{y≥x} Ly`; `ex = Tx / lx` ✔ | **New** |
| `nax` options | n/2 (even deaths) ✔; Greville `nax = n/2 − (n²/12)(nMx − k)`, `k = ln(M(x+n) / M(x−n)) / (2n)` ✔; Reed–Merrell `nqx = 1 − exp(−n·nMx − a·n³·nMx²)` with a ≈ 0.008 ◇; Coale–Demeny `a0`, `4a1` regression (Preston et al. 2001, Table 3.3) ◇; Keyfitz–Flieger ◇ | **New** |
| Complete life table | same columns by single year, from graduated data ✔ | **New** |
| Abridged life table | age groups 0, 1-4, 5-9, … ✔ | **New** |
| Probability of surviving to 65 | `l65 / l0` ✔ | **New** |
| Median age at death, modal age at death, life disparity ◇ | | **New** |
| Multiple decrement table | decrement by cause; associated single-decrement tables ◇ | **New** |
| Cause-eliminated life table ◇ | | **New** |
| Working life table | `working life expectancy at x = Σ_{y≥x} L_y × participation_y / l_x` (simple form) ◇ | **New** |
| Model life tables | Coale–Demeny regional (West, North, South, East), UN model tables, Brass logit relational: `logit(q(x)) = a + b × logit(q_std(x))` ✔ | **New (advanced)** |
| Relationships between functions | `Σ ndx = l0`, `l(x) = Σ ndx above x`, `mx = dx / Lx` ✔ | tests |

Why this is the biggest missing piece: B5 (real NRR), U5MR, stable-population analysis, projections and survival-ratio migration all need a female life table.

### 5.6 S6 Nuptiality

| Measure | Formula | Status |
|---|---|---|
| Marital status distribution | share never married / married / widowed / divorced / separated by age and sex ✔ | **New** |
| Crude marriage rate | `marriages / P × 1000` ✔ | **New** |
| General marriage rate | `marriages / population 15+ × 1000` (some books use unmarried 15+ only; pick one and say so) ◇ | **New** |
| Age-specific marriage rate | `marriages_i / P_i × 1000` ✔ | **New** |
| Total marriage rate | `n × Σ ASMR_i / 1000` ✔ | **New** |
| Total first marriage rate | same on first marriages ✔ | **New** |
| Singulate mean age at marriage (Hajnal) | `SMAM = (15 + 5 × Σ S_i − 50 × S50) / (1 − S50)`, `S_i` = proportion single in 15-19 … 45-49, `S50 = (S45-49 + S50-54) / 2` ✔ | **New** |
| Proportion ever married by 50 | `1 − S50` ✔ | **New** |
| Proportion never married at 45–49 (celibacy) | from marital status ✔ | **New** |
| Mean age at marriage (registration) | `Σ midpoint_i × marriages_i / Σ marriages_i` ✔ | **New** |
| Spousal age gap | `SMAM_male − SMAM_female` ✔ | **New** |
| Remarriage rate | `remarriages / (widowed + divorced) × 1000` ◇ | **New** |
| Crude divorce rate | `divorces / P × 1000` ✔ | **New** |
| General divorce rate | `divorces / married population × 1000` (refined: per married women 15+) ✔ | **New** (you named it) |
| Age-specific divorce rate | `divorces_i / married_i × 1000` ✔ | **New** |
| Total divorce rate | age-based `n × Σ ASDvR_i / 1000`, or duration-based sum of duration-specific rates ✔ | **New** (you named it) |
| Divorce-to-marriage ratio | `divorces / marriages × 100` ✔ | **New** |
| Widowhood: proportion widowed by age, widowhood rate | from marital status; rate = widowhood events / married ✔ | **New** |
| Separation: proportion separated by age | from marital status ✔ | **New** |
| Gross / net nuptiality tables (Hajnal) ◇ | | **New (advanced)** |
| Effect of marriage on fertility | Coale's `Im` ◇, Bongaarts `Cm` ◇; compare TFR with TMFR ✔ | **New** |

The SVRS (Bangladesh Sample Vital Registration System) has had marriage and migration modules since 1983, so your nuptiality and migration CSVs match what BBS actually publishes.

### 5.6b Age at marriage and fertility (syllabus line)

A small "what if" tool: shift the schedule of first marriage by +1, +2 years and show the effect on `Cm`/TFR. Uses the same inputs as S3 and S6.

### 5.7 S7 Migration

| Measure | Formula | Status |
|---|---|---|
| In-migration rate | `I / P × 1000` ✔ | **New** |
| Out-migration rate | `O / P × 1000` ✔ | **New** |
| Net migration rate | `(I − O) / P × 1000` ✔ | **New** |
| Gross migration rate (turnover) | `(I + O) / P × 1000` ✔ | **New** |
| Migration efficiency (effectiveness) ratio | `(I − O) / (I + O) × 100` ✔ | **New** |
| Residual (vital statistics) method | `NM = (P2 − P1) − (B − D)`; rate `= NM / mean(P1, P2) × 1000` ✔ | **New** |
| Life-table survival ratio method | `NM_x = P(x+n, t2) − S_x × P(x, t1)`, `S_x` from life table ✔ | **New** |
| Census survival ratio method | `S_x = P(x+n, t2) / P(x, t1)` in a reference area ✔ | **New** |
| Age-specific migration rates | `NM_x / P_x` ✔ | **New** |
| Lifetime migration (birthplace) | lifetime in-, out-, net migrants and rates ✔ | **New** |
| Migration streams, counter-streams | from OD matrix ✔ | **New** |
| Index of redistribution, index of preference / velocity / effectiveness ◇ (UN Manual VI; Shryock & Siegel) | | **New** |
| Urban–rural growth differential | `r_urban − r_rural` ✔ | **New** |
| Rogers–Castro model migration schedule ◇ | | **New (advanced)** |
| Gravity model | `flow_ij = k × P_i × P_j / d_ij^b` ◇ | **New (advanced, optional)** |
| Impact on age-sex structure | before/after pyramids using the net migration age schedule ✔ | **New** |

Syllabus items without a formula (migration laws, push–pull, effects on labour supply, wages, Bangladeshi migrants abroad): put them in an explanatory "Theory" card per section with a short reference list. Data for overseas migration comes from BMET and remittance data from Bangladesh Bank, not from the census.

### 5.8 S8 Graduation

| Method | Use |
|---|---|
| Sprague (osculatory) | 5-year groups → single years ✔ |
| Beers (ordinary, modified) | same, smoother ◇ |
| Karup–King | simple 3-group interpolation ✔ |
| Carrier–Farrag, Arriaga, Strong, Feeney | smoothing reported ages (reduce heaping) ◇ |
| Moving average / Spencer 15-point | general smoothing ◇ |
| Whittaker–Henderson | mortality rates ◇ |
| Gompertz–Makeham | parametric fit for adult mortality ◇ |

Coefficients: copy from a published table (UN Manual / Siegel & Swanson) and test the key property: **graduated single-year values re-sum to the original 5-year totals**.

### 5.9 S9 Stable & stationary

| Measure | Formula | Status |
|---|---|---|
| Lotka's equation | solve `Σ e^(−r·a_i) × f_female_i × L_i / l0 = 1` for `r` numerically (`a_i` = age-group midpoints) ✔ | **New** |
| Intrinsic birth rate | `b = 1 / Σ e^(−r·a_i) × L_i / l0` ✔ | **New** |
| Intrinsic death rate | `d = b − r` ✔ | **New** |
| Stable age distribution | `c(a) = b × e^(−r·a) × l(a) / l0` ✔ | **New** |
| Mean length of generation | `T ≈ ln(NRR) / r` ✔ | **New** |
| Stationary population | `r = 0`, `b = d = 1 / e0`, `c(a) = L(a) / T0` ✔ | **New** |
| Dominant eigenvalue of Leslie matrix | `λ = e^r` ✔ | **New** |
| Reproductive value, net maternity function ◇ | | **New (advanced)** |
| Population momentum (Keyfitz) ◇ | | **New (advanced)** |
| Estimating a stable population from two age distributions (Coale) ◇ | | **New (advanced)** |

### 5.10 S10 Transition & theory (explanatory, low priority)

- **Transition stage classifier**: rule-based from CBR, CDR, natural increase, TFR, `e0` → stage 1 to 4/5. Label clearly as heuristic.
- **Malthus demo**: population `P0 × (1+r)^t` against subsistence `S0 + k × t`; show crossing year. Teaching tool, not a forecast.
- Short cards for demographic transition (Notestein, Thompson) and the present Bangladesh situation, with citations.

### 5.11 S11 Projection

- **Cohort-component method** with a Leslie matrix: survive each age group with life-table ratios, apply ASFR × SRB to births, add net migration by age. Three scenarios by assumption files, not hardcoded constants.
- Simple extrapolations for comparison: linear, geometric, exponential, logistic.
- Uncertainty: scenario bands now, probabilistic later.
- Outputs: pyramids by year, dependency ratios by year, dividend window (working-age share and dependency ratio), births and deaths by year, TFR / e0 paths.
- Policy flags only from projected values crossing a documented threshold, each with the threshold and source printed.

---

## 6. Section output: what each report contains

Same layout for every section so the PDF and HTML code is shared:

1. Header: dataset, year, region, data source.
2. Input checks passed / warnings.
3. Assumptions used (empty is good).
4. Results table: measure, value, unit, method, formula, citation.
5. Charts (section-specific): pyramid, ASFR curve, `lx`/`qx` curves, marital status by age, migration flow chart, graduated vs raw.
6. Interpretation: sourced bands, marked heuristic where not sourced.
7. Short plain-language summary and top 3 concerns for that section.

Plus one **combined report** that stitches the sections you ran.

---

## 7. Data: make it real

Replace the synthetic "National Census" files with real Bangladesh data wherever you can. Candidates:

- **BBS Population and Housing Census 2011 and 2022** (age-sex, marital status, migration tables).
- **BBS Sample Vital Statistics (SVRS)** annual reports: age-specific fertility and mortality, marriage, migration modules (SVRS has used the Chandra Sekar–Deming dual-record system for registration).
- **BDHS** (Demographic and Health Survey) for fertility, child mortality, age at marriage.
- **UN World Population Prospects** and **UN IGME** for benchmarks and model schedules.
- **WHO Global Health Observatory** for benchmark bands.

Keep one small synthetic dataset **only** for tests, built so that every table sums to its stated total and the answers are known in advance.

Add a `DATA.md` listing source, table, year, licence, and any transformation you did.

---

## 8. Testing plan

- **Worked examples**: one per measure from your textbook (Bhende & Kanitkar, Shryock & Siegel, Preston et al., Rowland, UN Manuals). Put the book, chapter and page in the test docstring.
- **Cross-check with R** (you already use it): generate golden values with `DemoTools` (graduation, heaping indices, abridged life tables) and `demogR` (life tables), store as CSV fixtures, compare in pytest to 1e-6.
- **Properties**:
  - `TDR = CDR_child + OADR`
  - `Σ ndx = l0`
  - Sprague/Beers re-sum to original groups
  - stationary population: `b = d = 1/e0`
  - SMAM of an all-single population = 50; SMAM bounded by 15 and 50
  - `nqx` in [0, 1], `lx` non-increasing
  - `SMR == 1` only when rates equal the standard
- **Regression tests** for B1 to B12 (§1.5).
- **Schema tests**: every template CSV validates; every bad-file fixture gives the expected message.
- **CI**: pytest + ruff + mypy on every push.

---

## 9. Suggested order (broad → narrow)

| Phase | Goal | Done when |
|---|---|---|
| 0 | Correctness | B1–B12 fixed, regression tests pass, sample data consistent |
| 1 | Architecture | R1–R5: package layout, schemas, per-section loaders, result object, consistency checks |
| 2 | Mortality + life tables (S4, S5) | abridged and complete tables match R `demogR`/`DemoTools`; real NRR and U5MR |
| 3 | Nuptiality (S6) | SMAM, TMR, GDvR, TDvR tested; marital-status CSV flow in UI |
| 4 | Migration (S7) | residual, survival-ratio, rates, OD matrix, redistribution index |
| 5 | Graduation + stable/stationary (S8, S9) | multipliers re-sum; Lotka solver converges; Coale–Demeny check |
| 6 | Projection (S11), UI per section, reports, CI, docs | whole app runs from templates; combined report |
| 7 | Advanced extras | Coale/Bongaarts indices, Brass methods, multiple decrement, model tables |

If you only have time for a few things, do **Phase 0, Phase 1, Phase 2, Phase 3**. Those four turn this from a calculator demo into something a demographer would trust.

---

## 10. Docs to update when the code changes

- `README.md`: replace with the new one (already drafted alongside this file).
- `ENGINE.md` → `docs/METHODS.md`: one entry per measure with formula, inputs, assumptions, citation, test name.
- Fix counts (22 vs 23) and the Chandra Sekar–Deming citation.
- Add `docs/DATA.md` and `docs/CSV_SCHEMAS.md` (generated from the schema specs).

---

*Sources for the formula lists (web search): UN manuals on internal migration and census-data evaluation; Hajnal (1953) SMAM; Southampton eprint "Demographic measurement: nuptiality, mortality, migration and growth"; Coale–Demeny, Keyfitz–Flieger, Greville and Reed–Merrell life-table methods (documentation of R `demogR`, `DemogAnr`); BBS/GHDx records for SVRS. Items marked ◇ are the ones I could not confirm to the exact constant or form, so check your course book first.*
