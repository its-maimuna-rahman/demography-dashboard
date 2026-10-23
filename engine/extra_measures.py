"""
Additional measures from the class revision sheet ("Demography Revision Sheet: Measures & Topics").

Two kinds:
1. Computed automatically when the dataset has the inputs (percentage distribution, signed migration
   efficiency, intrinsic-rate moments, ...).
2. Input-driven calculators for measures that need figures a census table does not hold (cause-specific
   deaths, fetal deaths, order-of-birth counts, ...). Each is described by a CalcSpec so the UI can draw the
   inputs and a result card.

Nothing is guessed: a calculator returns None until every input it needs is valid.
"""

from __future__ import annotations
import math
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from engine.base import DemographicDataset, DemographicMeasureResult
from engine import registry

SHEET = "Class revision sheet (Demography Measures & Topics)"
BA, BB, BC, BD, BE, BF, BG, BH = (
    "A: Sex Composition & Growth", "B: Age Structure & Dependency", "C: Fertility & Reproduction",
    "D: Mortality & Standardization", "E: Life Tables", "F: Nuptiality & Marital Dynamics",
    "G: Migration & Spatial Redistribution", "H: Stable Population & Renewal",
)


def _reg(code, short, full, block, unit, formula, interp, decimals=2, cite=SHEET):
    registry.MEASURES_CATALOGUE[code] = {
        "code": code, "shortform": short, "full_name": full, "display_name": f"{full} ({short})", "block": block,
        "unit": unit, "formula": formula, "citation": cite, "interp_func": interp, "decimals": decimals,
    }


# ---------------------------------------------------------------- interpretations
def _i(text: str):
    """Build an interpretation function from a format string using {v} and context keys."""
    def f(v: float, ctx: Dict[str, Any]) -> str:
        return text.format(v=v, **{k: x for k, x in ctx.items() if isinstance(k, str)})
    return f


def _updown(v: float) -> str:
    return "an increase" if v > 0 else ("a decrease" if v < 0 else "no change")


# Composition
_reg("PCT_0_14", "%0-14", "Percentage Aged 0-14", BB, "% of population", "%P(0-14) = P(0-14) / P * 100",
     _i("Roughly {v:.2f}% of the population is under 15."))
_reg("PCT_15_64", "%15-64", "Percentage Aged 15-64", BB, "% of population", "%P(15-64) = P(15-64) / P * 100",
     _i("Roughly {v:.2f}% of the population is of working age (15-64)."))
_reg("PCT_65P", "%65+", "Percentage Aged 65 and Over", BB, "% of population", "%P(65+) = P(65+) / P * 100",
     _i("Roughly {v:.2f}% of the population is 65 or older."))
_reg("PCT_CHANGE", "%Δ", "Percentage Change", BA, "%", "%Δ = (New - Old) / Old * 100",
     lambda v, c: f"The value shows {_updown(v)} of {abs(v):.2f}% compared with the earlier figure.")
_reg("IRD", "IRD", "Index of Relative Difference (largest age group)", BB, "index", "IRD = | r2 / r1 * 100 - 100 |",
     _i("The share of the age group that differs most is {v:.2f}% higher or lower in one population than in the other."))
_reg("ID", "ID", "Index of Dissimilarity", BB, "%", "ID = 1/2 * sum |r2 - r1|",
     _i("About {v:.2f}% of one population would have to move to another age group for the two age distributions to match."))

# Fertility
_reg("RSOB", "RSOB", "Rate Specific to Order of Birth", BC, "births per 1,000 women 15-44", "RSOB = B_i / P^f(15-44) * 1000",
     _i("There are {v:.2f} births of this order per 1,000 women aged 15-44."))
_reg("DSFR", "DSFR", "Duration-Specific Marital Fertility Rate", BC, "births per 1,000 married women", "DSFR_t = B^m_t / P^{f,m}(15-44,t) * 1000",
     _i("There are {v:.2f} marital births per 1,000 married women aged 15-44 at this marriage duration."))
_reg("AABR_D", "AABR", "Age-Adjusted Birth Rate (direct)", BC, "births per 1,000", "AABR = sum( f_a * P^f_a ) / P * 1000",
     _i("If the population had the standard population's age structure, its birth rate would be {v:.2f} per 1,000."))
_reg("AABR_I", "AABR(ind)", "Age-Adjusted Birth Rate (indirect)", BC, "births per 1,000", "AABR_ind = b / sum( F_a * P^f_a ) * F",
     _i("Adjusted against the standard fertility schedule, the birth rate is {v:.2f} per 1,000."))
_reg("PROP_FEMALE_BIRTHS", "Bf/B", "Proportion of Births That Are Female", BC, "proportion", "Bf / B",
     lambda v, c: f"{v * 100:.2f}% of live births are girls.", decimals=4)
_reg("GRR_SHORT", "GRR(0.488)", "Gross Reproduction Rate (shortcut)", BC, "daughters per woman", "GRR = 0.488 * TFR",
     _i("Using the 0.488 shortcut, an average woman would have {v:.3f} daughters over her lifetime."), decimals=3)

# Mortality
_reg("CDR_AVG_V1", "CDR(avg1)", "Crude Death Rate, Multi-Year Average (version 1)", BD, "deaths per 1,000",
     "mean of yearly rates", _i("Averaging the yearly death rates gives {v:.3f} deaths per 1,000."), decimals=3)
_reg("CDR_AVG_V2", "CDR(avg2)", "Crude Death Rate, Multi-Year Average (version 2)", BD, "deaths per 1,000",
     "mean deaths / mean population * 1000", _i("Dividing average deaths by average population gives {v:.3f} deaths per 1,000."), decimals=3)
_reg("CDR_AVG_V3", "CDR(avg3)", "Crude Death Rate, Multi-Year Average (version 3)", BD, "deaths per 1,000",
     "mean deaths / mid-period population * 1000", _i("Dividing average deaths by the mid-period population gives {v:.3f} deaths per 1,000."), decimals=3)
_reg("MONTHLY_DR", "MDR", "Monthly Death Rate (annualised)", BD, "deaths per 1,000", "MDR = 365 / n_m * D_m / P_m * 1000",
     _i("Scaled up to a full year, the month's deaths imply {v:.2f} deaths per 1,000."))
_reg("ASDR_SEX", "ASDR(sex)", "Age-Sex Specific Death Rate", BD, "deaths per 1,000", "M^f_a = D^f_a / P^f_a * 1000",
     _i("There are {v:.2f} deaths per 1,000 people of this sex and age group."))
_reg("CSDR", "CSDR", "Cause-Specific Death Rate", BD, "deaths per 100,000", "CSDR = D_c / P * 100,000",
     _i("There are {v:.2f} deaths from this cause per 100,000 people."))
_reg("DEATH_RATIO", "DR(c)", "Death Ratio (share of deaths from a cause)", BD, "% of all deaths", "D_c / D * 100",
     _i("This cause accounts for {v:.2f}% of all deaths."))
_reg("ENDO_DR", "EnDR", "Endogenous Death Rate", BD, "deaths per 1,000", "D_en / P * 1000",
     _i("There are {v:.2f} deaths per 1,000 people from endogenous causes (chronic conditions that cannot be cured)."))
_reg("EXO_DR", "ExDR", "Exogenous Death Rate", BD, "deaths per 1,000", "D_ex / P * 1000",
     _i("There are {v:.2f} deaths per 1,000 people from exogenous causes (external effects such as infection)."))
_reg("CS_IMR", "CSIMR", "Cause-Specific Infant Death Rate", BD, "deaths per 100,000 births", "D^c_0 / B * 100,000",
     _i("There are {v:.2f} infant deaths from this cause per 100,000 live births."))
_reg("CSIMR_EN", "CSIMR(en)", "Cause-Specific IMR, Endogenous", BD, "deaths per 1,000 births", "D^en_0 / B * 1000",
     _i("{v:.2f} of every 1,000 live births die in infancy from endogenous causes."))
_reg("CSIMR_EX", "CSIMR(ex)", "Cause-Specific IMR, Exogenous", BD, "deaths per 1,000 births", "D^ex_0 / B * 1000",
     _i("{v:.2f} of every 1,000 live births die in infancy from exogenous causes."))
_reg("AIMR_A", "AIMR(A)", "Adjusted Infant Mortality Rate (formula A)", BD, "deaths per 1,000 births", "(D'_y + D''_{y+1}) / B_y * 1000",
     _i("Linking infant deaths to the year of birth (formula A), {v:.2f} of every 1,000 live births die in infancy."))
_reg("AIMR_B", "AIMR(B)", "Adjusted Infant Mortality Rate (formula B)", BD, "deaths per 1,000 births", "(D'_y / B_y + D''_y / B_{y-1}) * 1000",
     _i("Matching each group of infant deaths to its own birth year (formula B), the rate is {v:.2f} per 1,000 births."))
_reg("AIMR_C", "AIMR(C)", "Adjusted Infant Mortality Rate (formula C)", BD, "deaths per 1,000 births", "D_y / (f' B_y + (1 - f') B_{y-1}) * 1000",
     _i("Weighting births by the separation factor (formula C), the rate is {v:.2f} per 1,000 births."))
_reg("SEP_FACTOR", "f'", "Separation Factor", BD, "proportion", "f' = D'_y / (D'_y + D''_y)",
     lambda v, c: f"{v * 100:.1f}% of infant deaths come from births of the same year; the rest come from the previous year's births.", decimals=4)
_reg("PM_RATIO", "PMR", "Perinatal Mortality Ratio", BD, "per 1,000 live births", "(D_f + D_z) / B * 1000",
     _i("There are {v:.2f} fetal and early infant (under 1 week) deaths per 1,000 live births."))
_reg("PM_RATE", "PMRate", "Perinatal Mortality Rate", BD, "per 1,000 births incl. fetal deaths", "(D_f + D_z) / (D_f + B) * 1000",
     _i("There are {v:.2f} perinatal deaths per 1,000 births including fetal deaths."))
_reg("FD_RATIO", "FDR", "Fetal Death Ratio", BD, "per 1,000 live births", "D_f / B * 1000",
     _i("There are {v:.2f} fetal deaths per 1,000 live births."))
_reg("FD_RATE", "FDRate", "Fetal Death Rate", BD, "per 1,000 births incl. fetal deaths", "D_f / (D_f + B) * 1000",
     _i("There are {v:.2f} fetal deaths per 1,000 births including fetal deaths."))
_reg("MMRATE_NOTES", "MMR(1000)", "Maternal Mortality Rate (class-notes convention)", BD, "deaths per 1,000 births", "D_p / B * 1000",
     _i("There are {v:.2f} maternal deaths per 1,000 live births. The dashboard's MMR card uses the international convention of 100,000."))

# Life table (Reed-Merrell)
for _c, _s, _f, _fm in [
    ("RM_L0", "L0", "Reed-Merrell Person-Years, L0", "L0 = 0.276 l0 + 0.724 l1"),
    ("RM_4L1", "4L1", "Reed-Merrell Person-Years, 4L1", "4L1 = 0.034 l0 + 1.184 l1 + 2.782 l5"),
    ("RM_L1", "L1", "Person-Years, L1 (handwritten formula)", "L1 = 0.410 l1 + 0.590 l2"),
    ("RM_3L2", "3L2", "Person-Years, 3L2 (handwritten formula)", "3L2 = -0.021 l0 + 1.384 l2 + 1.637 l5"),
    ("RM_5L5", "5L5", "Person-Years, 5L5 (handwritten formula)", "5L5 = -0.003 l0 + 2.242 l5 + 2.761 l10"),
]:
    _reg(_c, _s, _f, BE, "person-years", _fm, _i(f"The estimated person-years lived in this interval ({_s}) is " + "{v:,.0f}."), decimals=0,
         cite="Reed & Merrell; class notes (check the handwritten formulas against your source)")

# Nuptiality
_reg("GMR", "GMR", "General Marriage Rate", BF, "marriages per 1,000 women 15+", "GMR = M / P^f(15+) * 1000",
     _i("There are {v:.2f} marriages per 1,000 women aged 15 and over."))
_reg("ASMR", "ASMR", "Age-Specific Marriage Rate", BF, "marriages per 1,000", "ASMR = M_age / P_age * 1000",
     _i("There are {v:.2f} marriages per 1,000 people in this age group."))
_reg("ASDVR", "ASDvR", "Age-Specific Divorce Rate", BF, "divorces per 1,000", "ASDvR = Div_age / P_age * 1000",
     _i("There are {v:.2f} divorces per 1,000 people in this age group."))
_reg("FMR", "FMR", "Final (First) Marriage Rate", BF, "first marriages per 1,000 never married", "M_1 / P^nm(15+) * 1000",
     _i("There are {v:.2f} first marriages per 1,000 never-married people aged 15+."))
_reg("REMARRIAGE_RATE", "RMR", "Second Marriage Rate", BF, "per 1,000 widowed and divorced", "M_2 / P(M+D) * 1000",
     _i("There are {v:.2f} second marriages per 1,000 widowed and divorced people."))
_reg("AOSMR", "AOSMR", "Age-Order Specific Marriage Rate", BF, "first marriages per 1,000", "M^{f,1}(20-24) / P^{f,nm,15+}(20-24) * 1000",
     _i("There are {v:.2f} first marriages per 1,000 never-married women in this age group."))
_reg("TMR", "TMR", "Total Marriage Rate (women)", BF, "marriages per 1,000 women", "TMR = sum( M^f_a / P^f_a ) * 1000",
     _i("Adding up age-specific marriage rates gives {v:.2f} marriages per 1,000 women over their lifetime."))
_reg("TFMR", "TFMR", "Total First Marriage Rate (women)", BF, "first marriages per 1,000 women", "TFMR = sum( M^{f,1}_a / P^f_a ) * 1000",
     _i("Adding up age-specific first-marriage rates gives {v:.2f} first marriages per 1,000 women over their lifetime."))
_reg("RDR", "RDR", "Refined Divorce Rate", BF, "divorces per 1,000 married women", "RDR = Div / P^f_m * 1000",
     _i("There are {v:.2f} divorces per 1,000 married women."))
_reg("DIV_DUR", "DvD", "Divorce Rate by Marriage Duration", BF, "divorces per 1,000 marriages", "Div_i / P_{m,i} * 1000",
     _i("There are {v:.2f} divorces per 1,000 marriages of this duration."))
_reg("MEDIAN_AGE_MARRIAGE", "MdAM", "Median Age at First Marriage (indirect)", BF, "years", "S(x) = (1 + S50) / 2, linear interpolation",
     _i("Half of the people who ever marry have done so by about age {v:.2f}."))

# Migration
_reg("IMRG", "IMRg", "In-Migration Rate", BG, "per 1,000", "IMR = I / P * 1000",
     _i("{v:.2f} people move in for every 1,000 residents each year."))
_reg("OMRG", "OMRg", "Out-Migration Rate", BG, "per 1,000", "OMR = O / P * 1000",
     _i("{v:.2f} people move out for every 1,000 residents each year."))
_reg("GROSS_MIG", "Gross", "Gross Migration", BG, "persons", "Gross = I + O",
     _i("There were {v:,.0f} moves in total, counting both arrivals and departures."))
_reg("NET_MIG", "Net", "Net Migration", BG, "persons", "Net = I - O",
     lambda v, c: f"Arrivals {'exceed' if v > 0 else ('fall short of' if v < 0 else 'equal')} departures by {abs(v):,.0f} persons.")
_reg("MER_SIGNED", "M.E.", "Migration Efficiency (signed)", BG, "%", "M.E. = (I - O) / (I + O) * 100",
     lambda v, c: ("Positive: out-migration is smaller than in-migration." if v > 0 else
                   ("Negative: in-migration is smaller than out-migration." if v < 0 else "Zero: in-migration equals out-migration.")) + f" The size, {abs(v):.2f}, shows how one-sided the movement is.")

# Stable population
_reg("R1", "R1", "First Moment of the Net Maternity Function", BH, "years", "R1 = integral x p(x) f(x) dx", _i("First moment of the net maternity function: the age-weighted total of expected daughters."), decimals=3)
_reg("R2", "R2", "Second Moment of the Net Maternity Function", BH, "years²", "R2 = integral x² p(x) f(x) dx", _i("Second moment: the squared-age-weighted total, used to measure how spread out childbearing is."))
_reg("ALPHA", "α", "Quadratic Parameter Alpha", BH, "years", "α = R1 / R0", _i("Equals the mean age of childbearing, {v:.3f} years."), decimals=3)
_reg("BETA", "β", "Quadratic Parameter Beta", BH, "years²", "β = (R1 / R0)² - R2 / R0", lambda v, c: f"The negative of the variance of the age at childbearing (variance = {-v:.2f} years squared).", decimals=3)
_reg("R_QUAD", "r(quad)", "Intrinsic Growth Rate, Quadratic Approximation", BH, "% per year", "r = (-α + sqrt(α² + 2β ln R0)) / β",
     lambda v, c: f"The quadratic approximation gives an intrinsic growth rate of {v:+.3f}% a year.", decimals=3)
_reg("T_QUAD", "T(quad)", "Mean Length of Generation, Quadratic", BH, "years", "T = α + 1/2 β r", _i("A generation is about {v:.2f} years by the quadratic formula."))
_reg("MU", "μ", "Mean Age of Childbearing (R1 / R0)", BH, "years", "μ = R1 / R0", _i("Weighted by survival, mothers are on average {v:.2f} years old at childbirth."))


# ---------------------------------------------------------------- results
def make_result(code: str, value: float, inputs: Optional[Dict[str, Any]] = None, notes: Optional[str] = None,
                ctx: Optional[Dict[str, Any]] = None) -> DemographicMeasureResult:
    meta = registry.MEASURES_CATALOGUE[code]
    dec = meta.get("decimals", 2)
    unit = meta["unit"]
    shown = f"{value:+,.{dec}f}" if code in ("NET_MIG",) else f"{value:,.{dec}f}"
    if code in ("PCT_0_14", "PCT_15_64", "PCT_65P", "PCT_CHANGE", "ID", "DEATH_RATIO", "MER_SIGNED"):
        shown += "%"
    return DemographicMeasureResult(
        code=code, shortform=meta["shortform"], full_name=meta["full_name"], name=meta["display_name"], block=meta["block"],
        raw_value=float(value), formatted_value=shown, unit=unit, formula=meta["formula"], citation=meta["citation"],
        plain_interpretation=meta["interp_func"](value, dict(ctx or {})), inputs_used=dict(inputs or {}), notes=notes,
    )


# ---------------------------------------------------------------- pure formulas
def _div(a: float, b: float) -> Optional[float]:
    return None if b is None or b <= 0 or a is None else a / b


def percentage_change(old: float, new: float) -> Optional[float]:
    return None if not old else (new - old) / old * 100.0


def percent_distribution(counts: Sequence[float]) -> np.ndarray:
    arr = np.asarray(counts, dtype=float)
    return arr / arr.sum() * 100.0 if arr.sum() > 0 else arr


def index_of_relative_difference(r1: Sequence[float], r2: Sequence[float]) -> np.ndarray:
    a, b = np.asarray(r1, dtype=float), np.asarray(r2, dtype=float)
    return np.where(a > 0, np.abs(b / np.where(a > 0, a, 1.0) * 100.0 - 100.0), np.nan)


def index_of_dissimilarity(r1: Sequence[float], r2: Sequence[float]) -> float:
    return float(0.5 * np.abs(np.asarray(r2, dtype=float) - np.asarray(r1, dtype=float)).sum())


def multi_year_cdr(deaths: Sequence[float], pops: Sequence[float]) -> Optional[Dict[str, float]]:
    """Three versions of the multi-year average CDR. The mid-period population is the middle year (odd n) or the mean of the two middle years (even n)."""
    d, p = np.asarray(deaths, dtype=float), np.asarray(pops, dtype=float)
    n = len(d)
    if n < 2 or len(p) != n or (p <= 0).any():
        return None
    mid = float(p[n // 2]) if n % 2 else float((p[n // 2 - 1] + p[n // 2]) / 2.0)
    return {
        "CDR_AVG_V1": float(np.mean(d / p) * 1000.0),
        "CDR_AVG_V2": float(d.mean() / p.mean() * 1000.0),
        "CDR_AVG_V3": float(d.mean() / mid * 1000.0),
    }


def aabr_direct(asfr_per_woman: Sequence[float], std_female_pop: Sequence[float], std_total_pop: float) -> Optional[float]:
    if std_total_pop <= 0:
        return None
    return float(np.dot(np.asarray(asfr_per_woman, dtype=float), np.asarray(std_female_pop, dtype=float)) / std_total_pop * 1000.0)


def aabr_indirect(births: float, std_cbr: float, std_asfr_per_woman: Sequence[float], study_female_pop: Sequence[float]) -> Optional[float]:
    expected = float(np.dot(np.asarray(std_asfr_per_woman, dtype=float), np.asarray(study_female_pop, dtype=float)))
    return None if expected <= 0 else births / expected * std_cbr


def total_rate(numerators: Sequence[float], denominators: Sequence[float], width: float = 1.0) -> Optional[float]:
    n, d = np.asarray(numerators, dtype=float), np.asarray(denominators, dtype=float)
    if len(n) == 0 or (d <= 0).any():
        return None
    return float((n / d).sum() * 1000.0 * width)


def median_age_at_first_marriage(single_props: Dict[str, float]) -> Optional[float]:
    """
    Indirect median age at first marriage from the proportion never married by 5-year age group.
    Each group's proportion is placed at the group's mid-point (consistent with the Hajnal SMAM person-years
    reading), S(15) is taken as 1, and S50 is the mean of the 45-49 and 50-54 groups. The median is the age at
    which S falls to (1 + S50) / 2, found by linear interpolation. This is an approximation.
    """
    groups = ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54"]
    if any(g not in single_props for g in groups):
        return None
    ages = [15.0] + [float(g.split("-")[0]) + 2.5 for g in groups]
    s = [1.0] + [float(single_props[g]) for g in groups]
    s50 = (single_props["45-49"] + single_props["50-54"]) / 2.0
    target = (1.0 + s50) / 2.0
    for i in range(1, len(s)):
        if s[i] <= target <= s[i - 1] and s[i - 1] != s[i]:
            return float(ages[i - 1] + (s[i - 1] - target) / (s[i - 1] - s[i]) * (ages[i] - ages[i - 1]))
    return None


def quadratic_stable_parameters(r0: float, r1: float, r2: float) -> Optional[Dict[str, float]]:
    """alpha, beta, quadratic r (per head) and T from the first two moments of the net maternity function."""
    if r0 <= 0:
        return None
    alpha = r1 / r0
    beta = alpha ** 2 - r2 / r0
    ln_r0 = math.log(r0)
    if abs(beta) < 1e-12:
        r = ln_r0 / alpha if alpha else float("nan")
    else:
        disc = alpha ** 2 + 2.0 * beta * ln_r0
        if disc < 0:
            return None
        r = (-alpha + math.sqrt(disc)) / beta
    return {"alpha": alpha, "beta": beta, "r": r, "T": alpha + 0.5 * beta * r, "mu": alpha}


# ---------------------------------------------------------------- dataset-driven extras
def _age_lower(label: str) -> Optional[int]:
    m = re.match(r"\s*(\d+)", str(label))
    return int(m.group(1)) if m else None


def compute_composition_extras(ds: DemographicDataset) -> Dict[str, DemographicMeasureResult]:
    out: Dict[str, DemographicMeasureResult] = {}
    p0, p1, p2, tot = ds.pop_0_14, ds.pop_15_64, ds.pop_65_plus, ds.total_population
    tbl = ds.age_group_5yr
    if (p0 is None or p1 is None or p2 is None) and tbl is not None and "total" in tbl.columns:
        lows = tbl["age_group"].map(_age_lower)
        p0 = float(tbl.loc[lows < 15, "total"].sum()); p2 = float(tbl.loc[lows >= 65, "total"].sum())
        p1 = float(tbl.loc[(lows >= 15) & (lows < 65), "total"].sum())
    if p0 is None or p1 is None or p2 is None:
        return out
    tot = tot or (p0 + p1 + p2)
    if tot <= 0:
        return out
    for code, val in (("PCT_0_14", p0), ("PCT_15_64", p1), ("PCT_65P", p2)):
        out[code] = make_result(code, val / tot * 100.0, {"group_population": val, "total_population": tot})
    return out


def compute_fertility_extras(ds: DemographicDataset, measures: Dict[str, DemographicMeasureResult]) -> Dict[str, DemographicMeasureResult]:
    out: Dict[str, DemographicMeasureResult] = {}
    fb, tb = ds.female_births, ds.total_live_births
    sched = ds.fertility_schedule
    if (fb is None) and sched is not None and "female_births" in sched.columns:
        fb, tb = float(sched["female_births"].sum()), float(sched["births"].sum())
    if fb is not None and tb and tb > 0:
        out["PROP_FEMALE_BIRTHS"] = make_result("PROP_FEMALE_BIRTHS", fb / tb, {"female_births": fb, "total_births": tb})
    if "TFR" in measures:
        out["GRR_SHORT"] = make_result("GRR_SHORT", 0.488 * measures["TFR"].raw_value, {"tfr": measures["TFR"].raw_value},
                                       notes="Shortcut used when only the TFR is available.")
    return out


def compute_migration_extras(in_m: float, out_m: float, pop: float) -> Dict[str, DemographicMeasureResult]:
    out: Dict[str, DemographicMeasureResult] = {}
    if pop and pop > 0:
        out["IMRG"] = make_result("IMRG", in_m / pop * 1000.0, {"in_migrants": in_m, "population": pop})
        out["OMRG"] = make_result("OMRG", out_m / pop * 1000.0, {"out_migrants": out_m, "population": pop})
    out["GROSS_MIG"] = make_result("GROSS_MIG", in_m + out_m, {"in_migrants": in_m, "out_migrants": out_m})
    out["NET_MIG"] = make_result("NET_MIG", in_m - out_m, {"in_migrants": in_m, "out_migrants": out_m})
    if in_m + out_m > 0:
        out["MER_SIGNED"] = make_result("MER_SIGNED", (in_m - out_m) / (in_m + out_m) * 100.0, {"in_migrants": in_m, "out_migrants": out_m})
    return out


def compute_nuptiality_extras(ds: DemographicDataset) -> Dict[str, DemographicMeasureResult]:
    out: Dict[str, DemographicMeasureResult] = {}
    tbl = ds.age_group_5yr
    if ds.marriages_total and tbl is not None and "female" in tbl.columns:
        lows = tbl["age_group"].map(_age_lower)
        f15 = float(tbl.loc[lows >= 15, "female"].sum())
        if f15 > 0:
            out["GMR"] = make_result("GMR", ds.marriages_total / f15 * 1000.0, {"marriages": ds.marriages_total, "women_15_plus": f15})
    mdf = ds.marital_status_df
    if mdf is not None and not mdf.empty and "sex" in mdf.columns:
        for sex, code_suffix in (("female", "F"), ("male", "M")):
            sub = mdf[mdf["sex"].astype(str).str.lower() == sex]
            if sub.empty:
                continue
            cols = [c for c in ["never_married", "single", "married", "widowed", "divorced", "separated"] if c in sub.columns]
            tot = sub[cols].sum(axis=1)
            sc = "never_married" if "never_married" in sub.columns else "single"
            props = dict(zip(sub["age_group"].astype(str).str.strip(), (sub[sc] / tot).astype(float)))
            med = median_age_at_first_marriage(props)
            if med is not None and sex == "female":
                out["MEDIAN_AGE_MARRIAGE"] = make_result("MEDIAN_AGE_MARRIAGE", med, {"sex": sex},
                                                         notes="Female median age at first marriage; proportions placed at group mid-points.")
    return out


def compute_extras_for_pipeline(ds: DemographicDataset, measures: Dict[str, DemographicMeasureResult]) -> Dict[str, DemographicMeasureResult]:
    out: Dict[str, DemographicMeasureResult] = {}
    out.update(compute_composition_extras(ds))
    out.update(compute_fertility_extras(ds, measures))
    out.update(compute_nuptiality_extras(ds))
    return out


# ---------------------------------------------------------------- calculator specs (input-driven measures)
@dataclass
class CalcInput:
    key: str
    label: str
    default: float = 0.0
    prefill: Optional[Callable[[DemographicDataset], Optional[float]]] = None
    help: str = ""


@dataclass
class CalcSpec:
    code: str
    group: str
    inputs: List[CalcInput]
    compute: Callable[[Dict[str, float]], Optional[float]]
    note: str = ""


def _pos(*vals: float) -> bool:
    return all(v is not None and v > 0 for v in vals)


_births = lambda ds: ds.total_live_births
_pop = lambda ds: ds.total_population
_deaths = lambda ds: ds.total_deaths

CALCULATORS: Dict[str, List[CalcSpec]] = {
    "mortality": [
        CalcSpec("MONTHLY_DR", "General rates", [CalcInput("n_m", "Days in the month", 30.0), CalcInput("d_m", "Deaths in the month"), CalcInput("p_m", "Population in the month")],
                 lambda v: 365.0 / v["n_m"] * v["d_m"] / v["p_m"] * 1000.0 if _pos(v["n_m"], v["p_m"]) and v["d_m"] >= 0 else None),
        CalcSpec("ASDR_SEX", "General rates", [CalcInput("d", "Deaths of this sex and age"), CalcInput("p", "Population of this sex and age")],
                 lambda v: v["d"] / v["p"] * 1000.0 if _pos(v["p"]) else None),
        CalcSpec("CSDR", "General rates", [CalcInput("d_c", "Deaths from the cause"), CalcInput("p", "Population", prefill=_pop)],
                 lambda v: v["d_c"] / v["p"] * 100000.0 if _pos(v["p"]) else None),
        CalcSpec("DEATH_RATIO", "General rates", [CalcInput("d_c", "Deaths from the cause"), CalcInput("d", "All deaths", prefill=_deaths)],
                 lambda v: v["d_c"] / v["d"] * 100.0 if _pos(v["d"]) else None),
        CalcSpec("ENDO_DR", "General rates", [CalcInput("d_en", "Endogenous deaths"), CalcInput("p", "Population", prefill=_pop)],
                 lambda v: v["d_en"] / v["p"] * 1000.0 if _pos(v["p"]) else None,
                 note="Endogenous: chronic disease, not curable."),
        CalcSpec("EXO_DR", "General rates", [CalcInput("d_ex", "Exogenous deaths"), CalcInput("p", "Population", prefill=_pop)],
                 lambda v: v["d_ex"] / v["p"] * 1000.0 if _pos(v["p"]) else None,
                 note="Exogenous: caused by external effects such as infection."),
        CalcSpec("CS_IMR", "Infant mortality", [CalcInput("d0c", "Infant deaths from the cause"), CalcInput("b", "Live births", prefill=_births)],
                 lambda v: v["d0c"] / v["b"] * 100000.0 if _pos(v["b"]) else None),
        CalcSpec("CSIMR_EN", "Infant mortality", [CalcInput("d0", "Endogenous infant deaths"), CalcInput("b", "Live births", prefill=_births)],
                 lambda v: v["d0"] / v["b"] * 1000.0 if _pos(v["b"]) else None),
        CalcSpec("CSIMR_EX", "Infant mortality", [CalcInput("d0", "Exogenous infant deaths"), CalcInput("b", "Live births", prefill=_births)],
                 lambda v: v["d0"] / v["b"] * 1000.0 if _pos(v["b"]) else None),
        CalcSpec("SEP_FACTOR", "Infant mortality", [CalcInput("d1", "D′: infant deaths linked to births of year y"), CalcInput("d2", "D″: infant deaths linked to births of year y−1")],
                 lambda v: v["d1"] / (v["d1"] + v["d2"]) if _pos(v["d1"] + v["d2"]) else None),
        CalcSpec("AIMR_A", "Infant mortality", [CalcInput("d1", "D′ in year y"), CalcInput("d2", "D″ in year y+1"), CalcInput("b", "Births in year y")],
                 lambda v: (v["d1"] + v["d2"]) / v["b"] * 1000.0 if _pos(v["b"]) else None),
        CalcSpec("AIMR_B", "Infant mortality", [CalcInput("d1", "D′ in year y"), CalcInput("b1", "Births in year y"), CalcInput("d2", "D″ in year y"), CalcInput("b0", "Births in year y−1")],
                 lambda v: (v["d1"] / v["b1"] + v["d2"] / v["b0"]) * 1000.0 if _pos(v["b1"], v["b0"]) else None),
        CalcSpec("AIMR_C", "Infant mortality", [CalcInput("d1", "D′ in year y"), CalcInput("d2", "D″ in year y"), CalcInput("b1", "Births in year y"), CalcInput("b0", "Births in year y−1")],
                 lambda v: (v["d1"] + v["d2"]) / ((v["d1"] / (v["d1"] + v["d2"])) * v["b1"] + (1 - v["d1"] / (v["d1"] + v["d2"])) * v["b0"]) * 1000.0
                 if _pos(v["d1"] + v["d2"], v["b1"], v["b0"]) else None),
        CalcSpec("PM_RATIO", "Perinatal, fetal and maternal", [CalcInput("df", "Fetal deaths"), CalcInput("dz", "Infant deaths under 1 week"), CalcInput("b", "Live births", prefill=_births)],
                 lambda v: (v["df"] + v["dz"]) / v["b"] * 1000.0 if _pos(v["b"]) else None),
        CalcSpec("PM_RATE", "Perinatal, fetal and maternal", [CalcInput("df", "Fetal deaths"), CalcInput("dz", "Infant deaths under 1 week"), CalcInput("b", "Live births", prefill=_births)],
                 lambda v: (v["df"] + v["dz"]) / (v["df"] + v["b"]) * 1000.0 if _pos(v["b"]) else None),
        CalcSpec("FD_RATIO", "Perinatal, fetal and maternal", [CalcInput("df", "Fetal deaths"), CalcInput("b", "Live births", prefill=_births)],
                 lambda v: v["df"] / v["b"] * 1000.0 if _pos(v["b"]) else None),
        CalcSpec("FD_RATE", "Perinatal, fetal and maternal", [CalcInput("df", "Fetal deaths"), CalcInput("b", "Live births", prefill=_births)],
                 lambda v: v["df"] / (v["df"] + v["b"]) * 1000.0 if _pos(v["b"]) else None,
                 note="Fetal deaths by gestation: under 20 weeks early; 20-27 intermediate; 28 weeks and over late."),
        CalcSpec("MMRATE_NOTES", "Perinatal, fetal and maternal", [CalcInput("dp", "Maternal deaths", prefill=lambda ds: ds.maternal_deaths), CalcInput("b", "Live births", prefill=_births)],
                 lambda v: v["dp"] / v["b"] * 1000.0 if _pos(v["b"]) else None,
                 note="The notes use ×1000. Many textbooks use ×100,000, as the MMR card above does."),
    ],
    "fertility": [
        CalcSpec("RSOB", "Fertility rates", [CalcInput("b_i", "Births of order i"), CalcInput("p", "Women aged 15-44")],
                 lambda v: v["b_i"] / v["p"] * 1000.0 if _pos(v["p"]) else None),
        CalcSpec("DSFR", "Fertility rates", [CalcInput("bm", "Marital births at duration t"), CalcInput("p", "Married women 15-44 at duration t")],
                 lambda v: v["bm"] / v["p"] * 1000.0 if _pos(v["p"]) else None),
    ],
    "lifetable": [
        CalcSpec("RM_L0", "Reed-Merrell person-years", [CalcInput("l0", "l0", 100000.0), CalcInput("l1", "l1")],
                 lambda v: 0.276 * v["l0"] + 0.724 * v["l1"] if _pos(v["l0"], v["l1"]) else None),
        CalcSpec("RM_4L1", "Reed-Merrell person-years", [CalcInput("l0", "l0", 100000.0), CalcInput("l1", "l1"), CalcInput("l5", "l5")],
                 lambda v: 0.034 * v["l0"] + 1.184 * v["l1"] + 2.782 * v["l5"] if _pos(v["l0"], v["l1"], v["l5"]) else None),
        CalcSpec("RM_L1", "Reed-Merrell person-years", [CalcInput("l1", "l1"), CalcInput("l2", "l2")],
                 lambda v: 0.410 * v["l1"] + 0.590 * v["l2"] if _pos(v["l1"], v["l2"]) else None,
                 note="Handwritten in the notes. Check against your source."),
        CalcSpec("RM_3L2", "Reed-Merrell person-years", [CalcInput("l0", "l0", 100000.0), CalcInput("l2", "l2"), CalcInput("l5", "l5")],
                 lambda v: -0.021 * v["l0"] + 1.384 * v["l2"] + 1.637 * v["l5"] if _pos(v["l0"], v["l2"], v["l5"]) else None,
                 note="Handwritten in the notes. Check against your source."),
        CalcSpec("RM_5L5", "Reed-Merrell person-years", [CalcInput("l0", "l0", 100000.0), CalcInput("l5", "l5"), CalcInput("l10", "l10")],
                 lambda v: -0.003 * v["l0"] + 2.242 * v["l5"] + 2.761 * v["l10"] if _pos(v["l0"], v["l5"], v["l10"]) else None,
                 note="Handwritten in the notes. Check against your source."),
    ],
    "nuptiality": [
        CalcSpec("ASMR", "Marriage and divorce rates", [CalcInput("m", "Marriages in the age group"), CalcInput("p", "Population in the age group")],
                 lambda v: v["m"] / v["p"] * 1000.0 if _pos(v["p"]) else None),
        CalcSpec("ASDVR", "Marriage and divorce rates", [CalcInput("d", "Divorces in the age group"), CalcInput("p", "Population in the age group")],
                 lambda v: v["d"] / v["p"] * 1000.0 if _pos(v["p"]) else None),
        CalcSpec("FMR", "Marriage and divorce rates", [CalcInput("m1", "First marriages"), CalcInput("p", "Never-married population aged 15+")],
                 lambda v: v["m1"] / v["p"] * 1000.0 if _pos(v["p"]) else None,
                 note="The notes call this the final marriage rate; it is probably meant as the first marriage rate."),
        CalcSpec("REMARRIAGE_RATE", "Marriage and divorce rates", [CalcInput("m2", "Second marriages"), CalcInput("p", "Widowed plus divorced population")],
                 lambda v: v["m2"] / v["p"] * 1000.0 if _pos(v["p"]) else None),
        CalcSpec("AOSMR", "Marriage and divorce rates", [CalcInput("m", "First marriages of women aged 20-24"), CalcInput("p", "Never-married women aged 20-24")],
                 lambda v: v["m"] / v["p"] * 1000.0 if _pos(v["p"]) else None),
        CalcSpec("RDR", "Marriage and divorce rates", [CalcInput("d", "Divorces"), CalcInput("p", "Married women")],
                 lambda v: v["d"] / v["p"] * 1000.0 if _pos(v["p"]) else None),
        CalcSpec("DIV_DUR", "Marriage and divorce rates", [CalcInput("d", "Divorces at duration i"), CalcInput("p", "Marriages of duration i")],
                 lambda v: v["d"] / v["p"] * 1000.0 if _pos(v["p"]) else None),
        CalcSpec("GMR", "Marriage and divorce rates", [CalcInput("m", "Marriages"), CalcInput("p", "Women aged 15+")],
                 lambda v: v["m"] / v["p"] * 1000.0 if _pos(v["p"]) else None),
    ],
    "composition": [
        CalcSpec("PCT_CHANGE", "Change over time", [CalcInput("old", "Old value"), CalcInput("new", "New value")],
                 lambda v: percentage_change(v["old"], v["new"]) if _pos(v["old"]) else None),
    ],
}


def evaluate(spec: CalcSpec, values: Dict[str, float]) -> Optional[DemographicMeasureResult]:
    try:
        val = spec.compute({k: float(x) for k, x in values.items()})
    except (ZeroDivisionError, ValueError, TypeError):
        return None
    if val is None or not math.isfinite(val):
        return None
    ctx: Dict[str, Any] = {}
    return make_result(spec.code, val, dict(values), notes=spec.note or None, ctx=ctx)


# Measures that need user-entered inputs or a second table are offered as calculators, not counted as "computed from the dataset".
_CALC_ONLY = {spec.code for specs in CALCULATORS.values() for spec in specs} - {"GMR"}
_CALC_ONLY |= {"CDR_AVG_V1", "CDR_AVG_V2", "CDR_AVG_V3", "AABR_D", "AABR_I", "IRD", "ID", "TMR", "TFMR", "PCT_CHANGE"}


def dataset_computable_count() -> int:
    return len([c for c in registry.MEASURES_CATALOGUE if c not in _CALC_ONLY])
