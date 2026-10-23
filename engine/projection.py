"""
Section 11: Cohort-Component Population Projection Engine
Replaces heuristic constants with true demographic cohort-component projection (Leslie / Life-Table Survival Matrix).

Methodology:
1. Base population disaggregated by 5-year age-sex cohorts (0-4, 5-9, ..., 85+)
2. Cohort survival forward shift using life-table survival ratios: S_x = 5L_{x+5} / 5L_x
3. Births generation over 5-year step using maternal ASFR schedules and mid-step person-years
4. Sex disaggregation of births via Sex Ratio at Birth (SRB ~105)
5. Infant cohort survival: P_{0-4}(t+5) = Births * (5L_0 / (5 * l0)) + Net Migration
6. Three Scenarios: Low, Medium, High fertility trajectories
7. Demographic Dividend Window tracking (Working-age share >= 60%)
8. Prescriptive policy screening flags tied to international benchmark thresholds

References:
- Preston, S. H., Heuveline, P., & Guillot, M. (2001). Demography, Ch. 6.
- United Nations Population Division (2022). World Population Prospects: Methodology of the UN Population Estimates and Projections.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Union
import math
import numpy as np
import pandas as pd

from engine.lifetable import build_abridged_life_table


@dataclass
class PolicyFlag:
    title: str
    severity: str  # 'INFO', 'WARNING', 'CONCERNING', 'CRITICAL'
    inflection_year: Optional[int]
    description: str
    rationale: str
    policy_recommendations: List[str]


@dataclass
class CohortComponentProjectionResult:
    scenario_name: str
    base_year: int
    horizon_years: int
    projection_years: List[int]
    total_population_series: pd.Series
    summary_df: pd.DataFrame
    combined_df: pd.DataFrame
    dividend_start_year: Optional[int]
    dividend_end_year: Optional[int]
    dividend_status: str
    policy_flags: List[PolicyFlag]
    narrative_policy_brief: str
    assumptions_summary: List[str]
    plain_interpretations: List[Dict[str, str]]
    projected_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    current_phase: str = "Demographic Dividend / Maturing Transition"


STD_GROUPS = [
    "0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39",
    "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80-84", "85+",
]
FERT_GROUPS = ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49"]
SCENARIO_ULTIMATE_MULTIPLIER = {"low": 0.82, "medium": 1.0, "high": 1.18}
REPLACEMENT_TFR = 2.1

# Reference shapes used ONLY when a caller supplies no tables (levels are then calibrated to the history).
REFERENCE_AGE_WEIGHTS = [0.08, 0.08, 0.08, 0.09, 0.09, 0.09, 0.08, 0.07, 0.06, 0.06, 0.05, 0.05, 0.04, 0.03, 0.02, 0.015, 0.01, 0.005]
REFERENCE_ASFR_PATTERN = [0.10, 0.32, 0.30, 0.18, 0.07, 0.025, 0.005]
REFERENCE_ASDR = [5.0, 0.6, 0.5, 1.0, 1.4, 1.7, 2.2, 3.1, 4.6, 6.8, 10.3, 15.6, 24.1, 37.0, 57.5, 88.0, 135.0, 215.0]


def schedule_tfr(fertility_schedule: pd.DataFrame) -> float:
    """TFR implied by a fertility schedule with columns age_group, female_pop, births."""
    return float(sum(5.0 * float(r["births"]) / float(r["female_pop"]) for _, r in fertility_schedule.iterrows()
                     if float(r["female_pop"]) > 0))


def _asfr_by_group(fertility_schedule: pd.DataFrame) -> Dict[str, float]:
    asfr = {str(r["age_group"]).strip(): float(r["births"]) / float(r["female_pop"])
            for _, r in fertility_schedule.iterrows() if float(r["female_pop"]) > 0}
    missing = [g for g in FERT_GROUPS if g not in asfr]
    if missing:
        raise ValueError(f"Fertility schedule is missing age groups: {', '.join(missing)}. Expected 15-19 through 45-49.")
    return asfr


def scale_age_structure_to_shares(base_df: pd.DataFrame, total: float, pct_youth: float, pct_working: float, pct_elderly: float) -> pd.DataFrame:
    """Rescale an age-sex table so its total and broad age shares (0-14, 15-64, 65+) match observed values."""
    df = base_df.copy()
    for c in ("male", "female"):
        df[c] = df[c].astype(float)
    df["total"] = df["male"] + df["female"]
    shares = {"y": pct_youth, "w": pct_working, "e": pct_elderly}
    norm = sum(shares.values())
    idx = {"y": range(0, 3), "w": range(3, 13), "e": range(13, 18)}
    for key, rng in idx.items():
        rows = [i for i in rng if i < len(df)]
        cur = float(df.iloc[rows]["total"].sum())
        target = total * shares[key] / norm
        if cur > 0:
            f = target / cur
            for col in ["male", "female", "total"]:
                if col in df.columns:
                    df.iloc[rows, df.columns.get_loc(col)] = df.iloc[rows][col].astype(float) * f
    return df


def scale_fertility_to_tfr(fertility_schedule: pd.DataFrame, target_tfr: float) -> pd.DataFrame:
    df = fertility_schedule.copy()
    df["births"] = df["births"].astype(float)
    cur = schedule_tfr(df)
    if cur > 0 and target_tfr > 0:
        df["births"] = df["births"] * (target_tfr / cur)
    return df


def _e0_of(mortality_schedule: pd.DataFrame) -> float:
    _, ind = build_abridged_life_table(mortality_schedule)
    return float(ind["E0"].raw_value)


def scale_mortality_to_e0(mortality_schedule: pd.DataFrame, target_e0: float) -> pd.DataFrame:
    """Scale the overall level of mortality (a single multiplier on deaths) so that e0 matches the target."""
    df = mortality_schedule.copy()
    df["deaths"] = df["deaths"].astype(float)
    lo, hi = 0.05, 8.0
    base_deaths = df["deaths"].copy()
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        df["deaths"] = base_deaths * mid
        if _e0_of(df) > target_e0:
            lo = mid
        else:
            hi = mid
    df["deaths"] = base_deaths * math.sqrt(lo * hi)
    return df


def run_cohort_component_projection(
    base_age_sex_df: pd.DataFrame,
    fertility_schedule: pd.DataFrame,
    mortality_schedule: pd.DataFrame,
    base_year: int = 2024,
    horizon_years: int = 30,
    scenario: str = "medium",  # 'medium', 'low', 'high'
    srb: float = 105.0,        # male births per 100 female births
    net_migration_annual: float = 0.0,
    tfr_targets: Optional[Dict[str, float]] = None,
    convergence_years: int = 15,
) -> CohortComponentProjectionResult:
    """
    Standard multi-cohort component projection over 5-year steps.

    Fertility follows a path that starts at the observed schedule and converges linearly over
    ``convergence_years`` to the scenario level (``tfr_targets[scenario]`` if given, otherwise the
    observed TFR times 0.82 / 1.00 / 1.18 for low / medium / high).
    """
    if scenario not in SCENARIO_ULTIMATE_MULTIPLIER:
        raise ValueError("scenario must be 'low', 'medium' or 'high'.")
    if horizon_years <= 0:
        raise ValueError("horizon_years must be positive.")

    df_base = base_age_sex_df.copy()
    if "male" not in df_base.columns or "female" not in df_base.columns:
        raise ValueError("Projection needs a base age table with 'male' and 'female' columns.")
    df_base["age_group"] = df_base["age_group"].astype(str).str.strip()
    n_groups = len(STD_GROUPS)

    # Survival ratios from the life table: S_x = 5L(x+5) / 5L(x)
    lt_fem, _ = build_abridged_life_table(mortality_schedule, sex="female")
    lt_male, _ = build_abridged_life_table(mortality_schedule, sex="male")
    L_fem, L_male = lt_fem["nLx"].values, lt_male["nLx"].values
    T_fem, T_male = lt_fem["Tx"].values, lt_male["Tx"].values
    if len(L_fem) < n_groups:
        raise ValueError(f"Mortality schedule needs all {n_groups} age groups (0-4 ... 85+); found {len(L_fem)}.")

    s_fem, s_male = np.zeros(n_groups), np.zeros(n_groups)
    for i in range(n_groups - 1):
        s_fem[i] = L_fem[i + 1] / L_fem[i] if L_fem[i] > 0 else 0.0
        s_male[i] = L_male[i + 1] / L_male[i] if L_male[i] > 0 else 0.0
    # Open interval 85+: survival approximated as T85 / T80
    s_fem[-1] = T_fem[-1] / (T_fem[-1] + L_fem[-2]) if (T_fem[-1] + L_fem[-2]) > 0 else 0.0
    s_male[-1] = T_male[-1] / (T_male[-1] + L_male[-2]) if (T_male[-1] + L_male[-2]) > 0 else 0.0
    s0_fem = L_fem[0] / (5.0 * 100000.0)
    s0_male = L_male[0] / (5.0 * 100000.0)

    asfr = _asfr_by_group(fertility_schedule)
    base_tfr = 5.0 * sum(asfr[g] for g in FERT_GROUPS)
    if tfr_targets and scenario in tfr_targets and base_tfr > 0:
        ultimate_mult = float(tfr_targets[scenario]) / base_tfr
    else:
        ultimate_mult = SCENARIO_ULTIMATE_MULTIPLIER[scenario]

    steps = int(math.ceil(horizon_years / 5.0))
    years = [base_year + step * 5 for step in range(steps + 1)]

    cur_m, cur_f = np.zeros(n_groups), np.zeros(n_groups)
    for i, g in enumerate(STD_GROUPS):
        row = df_base[df_base["age_group"] == g]
        if row.empty:
            raise ValueError(f"Base age table is missing age group '{g}'.")
        cur_m[i] = float(row["male"].values[0])
        cur_f[i] = float(row["female"].values[0])

    def snapshot(year: int, m: np.ndarray, f: np.ndarray, tfr: float, births: float, deaths: float) -> Dict[str, Any]:
        tot = m.sum() + f.sum()
        p0, p1, p2 = m[:3].sum() + f[:3].sum(), m[3:13].sum() + f[3:13].sum(), m[13:].sum() + f[13:].sum()
        return {
            "year": year, "total_population": tot, "male_population": m.sum(), "female_population": f.sum(),
            "pop_0_14": p0, "pop_15_64": p1, "pop_65_plus": p2,
            "pct_youth": p0 / tot * 100.0 if tot > 0 else 0.0,
            "pct_working_age": p1 / tot * 100.0 if tot > 0 else 0.0,
            "pct_elderly": p2 / tot * 100.0 if tot > 0 else 0.0,
            "total_dependency_ratio": (p0 + p2) / p1 * 100.0 if p1 > 0 else 0.0,
            "old_age_dependency_ratio": p2 / p1 * 100.0 if p1 > 0 else 0.0,
            "tfr": tfr, "births_5yr": births, "deaths_5yr": deaths,
        }

    records = [snapshot(base_year, cur_m, cur_f, base_tfr, np.nan, np.nan)]
    f_prob, m_prob = 100.0 / (100.0 + srb), srb / (100.0 + srb)

    for step in range(1, steps + 1):
        prev_m, prev_f = cur_m.copy(), cur_f.copy()
        progress = min(1.0, (step * 5.0) / max(1.0, float(convergence_years)))
        mult = 1.0 + (ultimate_mult - 1.0) * progress

        next_m, next_f = np.zeros(n_groups), np.zeros(n_groups)
        for i in range(n_groups - 2):
            next_m[i + 1] = prev_m[i] * s_male[i]
            next_f[i + 1] = prev_f[i] * s_fem[i]
        next_m[-1] = prev_m[-2] * s_male[-2] + prev_m[-1] * s_male[-1]
        next_f[-1] = prev_f[-2] * s_fem[-2] + prev_f[-1] * s_fem[-1]

        step_births = 0.0
        for g_idx in range(3, 10):
            fx = asfr[STD_GROUPS[g_idx]] * mult
            step_births += 5.0 * fx * (prev_f[g_idx] + next_f[g_idx]) / 2.0

        next_f[0] = step_births * f_prob * s0_fem
        next_m[0] = step_births * m_prob * s0_male

        net_5yr = net_migration_annual * 5.0
        if net_5yr != 0:
            # Net migrants are spread evenly over working ages 15-64 and by sex
            next_m[3:13] += (net_5yr * 0.5) / 10.0
            next_f[3:13] += (net_5yr * 0.5) / 10.0
            next_m, next_f = np.clip(next_m, 0, None), np.clip(next_f, 0, None)

        cur_m, cur_f = next_m, next_f
        tot_now = cur_m.sum() + cur_f.sum()
        deaths_5yr = max(0.0, (prev_m.sum() + prev_f.sum() + step_births + net_5yr) - tot_now)
        records.append(snapshot(base_year + step * 5, cur_m, cur_f, base_tfr * mult, step_births, deaths_5yr))

    proj_df = pd.DataFrame(records)
    proj_df["pct_working_15_64"] = proj_df["pct_working_age"]
    proj_df["pct_elderly_65_plus"] = proj_df["pct_elderly"]
    proj_df["oadr"] = proj_df["old_age_dependency_ratio"]

    # Demographic dividend window (working-age share >= 60%)
    div_start = div_end = None
    div_status = "Closed"
    above = proj_df[proj_df["pct_working_age"] >= 60.0]
    if not above.empty:
        div_start = int(above.iloc[0]["year"])
        below_after = proj_df[(proj_df["year"] > div_start) & (proj_df["pct_working_age"] < 60.0)]
        if not below_after.empty:
            div_end = int(below_after.iloc[0]["year"])
            div_status = f"Closing around {div_end}"
        else:
            div_status = "Open Throughout Horizon"

    flags: List[PolicyFlag] = []
    if div_end:
        flags.append(PolicyFlag(
            title=f"Demographic Dividend Window Closes (~{div_end})", severity="WARNING", inflection_year=div_end,
            description=f"Working-age share falls below 60% around {div_end}, raising dependency loads.",
            rationale="Threshold: working-age (15-64) share < 60% of total population.",
            policy_recommendations=[
                "Maximise youth skill formation and productivity before the window closes.",
                "Encourage pension capitalisation and formal female labour-force participation.",
            ]))
    elif div_status == "Open Throughout Horizon":
        flags.append(PolicyFlag(
            title="Demographic Dividend Window Stays Open", severity="INFO", inflection_year=div_start,
            description="Working-age share stays at or above 60% through the projection horizon.",
            rationale="Threshold: working-age (15-64) share >= 60% in every projected year.",
            policy_recommendations=[
                "Expand vocational and technical education for incoming workforce cohorts.",
                "Create productive formal jobs to absorb the large working-age population.",
            ]))
    aging = proj_df[proj_df["old_age_dependency_ratio"] >= 20.0]
    if not aging.empty:
        yr = int(aging.iloc[0]["year"])
        flags.append(PolicyFlag(
            title=f"Population Aging Inflection (OADR >= 20 around {yr})", severity="CONCERNING", inflection_year=yr,
            description=f"Old-age dependency exceeds 20 people aged 65+ per 100 workers around {yr}.",
            rationale="Threshold: OADR >= 20 per 100 persons aged 15-64.",
            policy_recommendations=[
                "Build sustainable contributory and universal pension schemes.",
                "Develop geriatric and long-term care capacity.",
            ]))
    sub = proj_df[proj_df["tfr"] < REPLACEMENT_TFR]
    if not sub.empty and base_tfr >= 0:
        yr = int(sub.iloc[0]["year"])
        flags.append(PolicyFlag(
            title=f"Fertility Below Replacement ({yr} onward)", severity="INFO" if yr == base_year else "WARNING",
            inflection_year=yr,
            description=f"Projected TFR is below 2.1 from {yr}, so each generation is smaller than the last once momentum fades.",
            rationale="Threshold: TFR < 2.1 children per woman.",
            policy_recommendations=[
                "Monitor the youth cohort entering school and labour-market ages.",
                "Plan long-run fiscal balance around slower labour-force growth.",
            ]))
    peak_idx = int(proj_df["total_population"].idxmax())
    if 0 < peak_idx < len(proj_df) - 1:
        yr = int(proj_df.loc[peak_idx, "year"])
        flags.append(PolicyFlag(
            title=f"Population Peaks Around {yr}", severity="CONCERNING", inflection_year=yr,
            description=f"Total population reaches its maximum of {proj_df.loc[peak_idx, 'total_population']:,.0f} around {yr} and then declines.",
            rationale="Threshold: projected total population falls in the years after the peak.",
            policy_recommendations=[
                "Prepare infrastructure and service planning for a stable then shrinking population.",
                "Review migration and labour-force participation policy.",
            ]))

    first, last = proj_df.iloc[0], proj_df.iloc[-1]
    end_year = int(last["year"])
    narrative = (
        f"Under the **{scenario.title()} Variant** over {horizon_years} years ({base_year}-{end_year}), "
        f"population moves from {first['total_population']:,.0f} to {last['total_population']:,.0f}. "
        f"The working-age share moves from {first['pct_working_age']:.1f}% to {last['pct_working_age']:.1f}%, "
        f"and TFR from {first['tfr']:.2f} to {last['tfr']:.2f}. Demographic dividend window: **{div_status}**."
    )
    assumptions = [
        f"Scenario: {scenario.title()}. TFR moves from the observed {base_tfr:.2f} to {base_tfr * ultimate_mult:.2f}, converging linearly over {convergence_years} years.",
        f"Sex ratio at birth held at {srb:.1f} male births per 100 female births.",
        "Survival ratios come from a period life table built from the supplied mortality schedule (5L(x+5)/5L(x); open interval 85+ uses T85/T80).",
        "Males and females share one both-sexes mortality schedule; only the infant separation factor differs by sex.",
        f"Net migration: {net_migration_annual:+,.0f} persons per year, spread evenly over ages 15-64 and both sexes.",
        "Projection runs in 5-year steps; annual values (when shown) are linear interpolations between steps.",
    ]
    plain = [
        {"title": "Population Trajectory", "interpretation": f"Population moves from {first['total_population']:,.0f} in {base_year} to {last['total_population']:,.0f} by {end_year}."},
        {"title": "Working-Age Share", "interpretation": f"The working-age cohort is {last['pct_working_age']:.1f}% of the population at the end of the horizon."},
        {"title": "Old-Age Dependency (OADR)", "interpretation": f"Old-age dependency reaches {last['old_age_dependency_ratio']:.1f} people aged 65+ per 100 workers at the end of the horizon."},
    ]
    return CohortComponentProjectionResult(
        scenario_name=f"{scenario.title()} Variant", base_year=base_year, horizon_years=horizon_years,
        projection_years=years, total_population_series=proj_df["total_population"], summary_df=proj_df,
        combined_df=proj_df, dividend_start_year=div_start, dividend_end_year=div_end, dividend_status=div_status,
        policy_flags=flags, narrative_policy_brief=narrative, assumptions_summary=assumptions, plain_interpretations=plain,
        projected_df=proj_df.iloc[1:].reset_index(drop=True),
        current_phase=_phase_label(first),
    )


def _phase_label(row: pd.Series) -> str:
    work, old, tfr = float(row["pct_working_age"]), float(row["pct_elderly"]), float(row["tfr"])
    if old >= 14:
        return "Aging Society"
    if work >= 60 and tfr < 2.5:
        return "Demographic Dividend / Maturing Transition"
    if tfr >= 3.5:
        return "Early Transition / Youthful Population"
    return "Mid Transition"


def simulate_demographic_trajectory(
    historical_df: pd.DataFrame,
    projection_horizon_years: int = 30,
    fertility_scenario: str = "medium",
    base_age_sex_df: Optional[pd.DataFrame] = None,
    fertility_schedule: Optional[pd.DataFrame] = None,
    mortality_schedule: Optional[pd.DataFrame] = None,
    srb: float = 105.0,
    net_migration_annual: float = 0.0,
    tfr_targets: Optional[Dict[str, float]] = None,
) -> CohortComponentProjectionResult:
    """
    Module 2 entry point: project forward from the last row of a historical time series.

    The base population, fertility pattern and mortality pattern come from the supplied tables
    (for example the census age-sex table and SVRS schedules). When a table is not supplied a
    reference shape is used instead. In both cases the LEVELS are calibrated to the latest
    observed row: total population, broad age shares, TFR and life expectancy. These choices
    are listed in ``assumptions_summary``.
    """
    hist = historical_df.copy()
    hist.columns = [str(c) for c in hist.columns]
    lower = {c.lower(): c for c in hist.columns}

    def col(*names: str) -> Optional[str]:
        for n in names:
            if n.lower() in lower:
                return lower[n.lower()]
        return None

    year_c = col("year")
    if year_c is None:
        raise ValueError("Historical series needs a 'year' column.")
    last = hist.iloc[-1]
    base_yr = int(last[year_c])
    tot_c = col("total_population")
    if tot_c is None:
        raise ValueError("Historical series needs a 'total_population' column.")
    tot_p = float(last[tot_c])

    tfr_c, e0_c = col("tfr"), col("life_expectancy", "e0")
    youth_c, work_c, eld_c = col("pct_youth", "pct_youth_0_14"), col("pct_working_age", "pct_working_15_64"), col("pct_elderly", "pct_elderly_65_plus")
    notes: List[str] = []

    # --- base age-sex table
    if base_age_sex_df is not None:
        base_df = base_age_sex_df.copy()
        if "male" not in base_df.columns or "female" not in base_df.columns:
            raise ValueError("base_age_sex_df needs 'male' and 'female' columns.")
        src = "supplied age-sex table"
    else:
        w = np.array(REFERENCE_AGE_WEIGHTS) / sum(REFERENCE_AGE_WEIGHTS)
        base_df = pd.DataFrame({"age_group": STD_GROUPS, "male": tot_p * w * 0.505, "female": tot_p * w * 0.495})
        src = "reference age shape"
    base_df["total"] = base_df["male"] + base_df["female"]
    if youth_c and work_c and eld_c:
        base_df = scale_age_structure_to_shares(base_df, tot_p, float(last[youth_c]), float(last[work_c]), float(last[eld_c]))
        notes.append(f"Base age structure ({src}) rescaled to the {base_yr} total population and broad age shares (0-14 / 15-64 / 65+) of the historical series.")
    else:
        base_df = base_df.copy()
        f = tot_p / base_df["total"].sum()
        for c in ["male", "female", "total"]:
            base_df[c] = base_df[c] * f
        notes.append(f"Base age structure ({src}) rescaled to the {base_yr} total population.")

    # --- fertility
    tfr_obs = float(last[tfr_c]) if tfr_c else None
    if fertility_schedule is not None:
        fert = fertility_schedule[["age_group", "female_pop", "births"]].copy()
        src_f = "supplied fertility schedule"
    else:
        fem = [float(base_df.iloc[i]["female"]) for i in range(3, 10)]
        t = tfr_obs if tfr_obs else 2.0
        fert = pd.DataFrame({"age_group": FERT_GROUPS, "female_pop": fem,
                             "births": [(t / 5.0) * wgt * pop for wgt, pop in zip(REFERENCE_ASFR_PATTERN, fem)]})
        src_f = "reference age pattern"
    if tfr_obs:
        fert = scale_fertility_to_tfr(fert, tfr_obs)
        notes.append(f"Fertility ({src_f}) scaled to the observed {base_yr} TFR of {tfr_obs:.2f}.")

    # --- mortality
    if mortality_schedule is not None:
        mort = mortality_schedule[["age_group", "population", "deaths"]].copy()
        src_m = "supplied mortality schedule"
    else:
        wts = np.array(REFERENCE_AGE_WEIGHTS) / sum(REFERENCE_AGE_WEIGHTS)
        mort = pd.DataFrame({"age_group": STD_GROUPS, "population": tot_p * wts,
                             "deaths": tot_p * wts * np.array(REFERENCE_ASDR) / 1000.0})
        src_m = "reference age pattern"
    if e0_c:
        e0_obs = float(last[e0_c])
        mort = scale_mortality_to_e0(mort, e0_obs)
        notes.append(f"Mortality ({src_m}) level calibrated so life expectancy at birth equals the observed {e0_obs:.1f} years.")

    res = run_cohort_component_projection(
        base_age_sex_df=base_df, fertility_schedule=fert, mortality_schedule=mort,
        base_year=base_yr, horizon_years=projection_horizon_years, scenario=fertility_scenario,
        srb=srb, net_migration_annual=net_migration_annual, tfr_targets=tfr_targets,
    )
    res.assumptions_summary = notes + res.assumptions_summary

    # --- annual series: linear interpolation between the 5-year steps
    steps_df = res.summary_df.drop(columns=["births_5yr", "deaths_5yr"], errors="ignore")
    annual_years = list(range(base_yr, base_yr + projection_horizon_years + 1))
    annual = pd.DataFrame({"year": annual_years})
    for c in steps_df.columns:
        if c == "year":
            continue
        annual[c] = np.interp(annual_years, steps_df["year"].values, steps_df[c].astype(float).values)
    annual = annual[annual["year"] > base_yr].reset_index(drop=True)
    annual["is_projected"] = True

    hist_clean = hist.copy()
    hist_clean["is_projected"] = False
    alias = {"tfr": tfr_c, "pct_working_15_64": work_c, "pct_elderly_65_plus": eld_c, "pct_youth": youth_c,
             "oadr": col("oadr", "old_age_dependency_ratio"), "old_age_dependency_ratio": col("old_age_dependency_ratio", "oadr"),
             "total_dependency_ratio": col("total_dependency_ratio", "tdr"), "pct_working_age": work_c, "pct_elderly": eld_c}
    for new, src_col in alias.items():
        if src_col and new not in hist_clean.columns:
            hist_clean[new] = hist_clean[src_col]
    res.projected_df = annual
    res.combined_df = pd.concat([hist_clean, annual], ignore_index=True)
    return res
