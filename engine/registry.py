"""
Demographic Measures Registry
Comprehensive central catalogue of demographic measures across all syllabus sections.
Ensures every measure has its shortform alongside its full form (e.g. Gross Reproduction Rate (GRR))
and provides dynamic, textbook-grade plain-language interpretation generators.
"""

from __future__ import annotations
from typing import Dict, Any, Callable, Optional


def _pl(val: float, singular: str, plural: str) -> str:
    return singular if abs(val - 1.0) < 1e-9 else plural


def _interpret_mp(val: float, ctx: Dict[str, Any]) -> str:
    return f"Roughly {val:.2f}% of the population is male. The remaining {max(0.0, 100.0 - val):.2f}% is female."

def _interpret_sr(val: float, ctx: Dict[str, Any]) -> str:
    per = ctx.get("per", 100)
    tail = "Women outnumber men." if val < 100 else ("Men outnumber women." if val > 100 else "The sexes are balanced.")
    return f"There are about {val:.2f} males for every {per} females. {tail}"

def _interpret_srb(val: float, ctx: Dict[str, Any]) -> str:
    return f"About {val:.1f} boys are born for every 100 girls. The usual biological range is 103 to 107."

def _interpret_excess_m(val: float, ctx: Dict[str, Any]) -> str:
    pct = abs(ctx.get("percent_excess", 0.0))
    if val > 0:
        return f"Males outnumber females by {val:,.0f} persons, {pct:.2f}% of the population."
    if val < 0:
        return f"Females outnumber males by {abs(val):,.0f} persons, {pct:.2f}% of the population."
    return "Males and females are equal in number."

def _interpret_acr(val: float, ctx: Dict[str, Any]) -> str:
    young, old = ctx.get("pct_0_14", 0.0), ctx.get("pct_65_plus", 0.0)
    return (f"Roughly {val:.2f}% of the population is of working age (15-64). "
            f"Children (0-14) are {young:.2f}% and people aged 65+ are {old:.2f}%.")

def _interpret_tdr(val: float, ctx: Dict[str, Any]) -> str:
    return f"For every 100 people of working age there are about {val:.2f} dependants (children under 15 plus people 65+). Higher values mean a heavier load on workers."

def _interpret_cdr_child(val: float, ctx: Dict[str, Any]) -> str:
    return f"About {val:.2f} children aged 0-14 depend on every 100 people of working age (15-64)."

def _interpret_oadr(val: float, ctx: Dict[str, Any]) -> str:
    return f"About {val:.2f} people aged 65+ depend on every 100 people of working age (15-64)."

def _interpret_ai(val: float, ctx: Dict[str, Any]) -> str:
    return f"There are {val:.2f} people aged 65+ for every 100 children under 15. Higher values mean an older population."

def _interpret_psr(val: float, ctx: Dict[str, Any]) -> str:
    return f"About {val:.2f} people of working age support each person aged 65+."

def _interpret_median_age(val: float, ctx: Dict[str, Any]) -> str:
    cls = "young" if val < 20 else ("intermediate" if val < 30 else "old")
    return f"Half of the population is younger than {val:.2f} years and half is older. By the usual rule (under 20 young, 20-29 intermediate, 30+ old) this is a {cls} population."

def _interpret_cwr(val: float, ctx: Dict[str, Any]) -> str:
    return f"There are {val:.2f} children aged 0-4 for every 1,000 women aged 15-49. It is a quick fertility indicator when birth records are weak."

def _interpret_density(val: float, ctx: Dict[str, Any]) -> str:
    return f"About {val:,.1f} people live on each square kilometre."

def _interpret_growth_rate(val: float, ctx: Dict[str, Any]) -> str:
    dt = ctx.get("doubling_time")
    dt_str = f" At this pace the population doubles in about {dt:.1f} years." if dt and dt > 0 else ""
    return f"The population is {'growing' if val >= 0 else 'shrinking'} by {abs(val):.2f}% a year.{dt_str}"

def _interpret_cbr(val: float, ctx: Dict[str, Any]) -> str:
    return f"There are {val:.2f} live births per 1,000 people in the year."

def _interpret_gfr(val: float, ctx: Dict[str, Any]) -> str:
    return f"There are {val:.2f} live births per 1,000 women aged 15-49."

def _interpret_asfr(val: float, ctx: Dict[str, Any]) -> str:
    peak_age = ctx.get("peak_age_group", "20-24")
    return f"Fertility peaks in the {peak_age} age group at {val:.1f} births per 1,000 women."

def _interpret_tfr(val: float, ctx: Dict[str, Any]) -> str:
    rep = "below" if val < 2.05 else ("at" if val <= 2.15 else "above")
    return f"An average woman would have {val:.2f} children over her lifetime at current rates. That is {rep} the replacement level of about 2.1."

def _interpret_grr(val: float, ctx: Dict[str, Any]) -> str:
    return f"An average woman would have {val:.3f} daughters over her lifetime, ignoring deaths before the end of childbearing."

def _interpret_nrr(val: float, ctx: Dict[str, Any]) -> str:
    traj = "grow" if val > 1.0 else ("shrink" if val < 1.0 else "stay the same size")
    cmp_ = "above" if val > 1.0 else ("below" if val < 1.0 else "equal to")
    return f"Each newborn girl is replaced by {val:.3f} daughters who survive to childbearing age. A value {cmp_} 1 means the population will eventually {traj}."

def _interpret_gmfr(val: float, ctx: Dict[str, Any]) -> str:
    return f"There are {val:.2f} live births per 1,000 married women aged 15-49."

def _interpret_mac(val: float, ctx: Dict[str, Any]) -> str:
    return f"On average, mothers are {val:.2f} years old when their children are born."

def _interpret_cdr(val: float, ctx: Dict[str, Any]) -> str:
    return f"There are {val:.2f} deaths per 1,000 people in the year."

def _interpret_ccdr(val: float, ctx: Dict[str, Any]) -> str:
    return f"After correcting for incomplete death registration and census coverage, the death rate is {val:.2f} per 1,000."

def _interpret_nmr(val: float, ctx: Dict[str, Any]) -> str:
    return f"{val:.2f} of every 1,000 live births die within the first 28 days of life."

def _interpret_enmr(val: float, ctx: Dict[str, Any]) -> str:
    return f"{val:.2f} of every 1,000 live births die within the first 7 days of life."

def _interpret_pnmr(val: float, ctx: Dict[str, Any]) -> str:
    return f"{val:.2f} of every 1,000 live births die between 28 days and the first birthday."

def _interpret_imr(val: float, ctx: Dict[str, Any]) -> str:
    return f"{val:.2f} of every 1,000 live births die before their first birthday."

def _interpret_cdr_1_4(val: float, ctx: Dict[str, Any]) -> str:
    return f"There are {val:.2f} deaths per 1,000 children aged 1-4 in a year."

def _interpret_u5mr(val: float, ctx: Dict[str, Any]) -> str:
    return f"About {val:.2f} of every 1,000 live births die before their fifth birthday."

def _interpret_mmr(val: float, ctx: Dict[str, Any]) -> str:
    return f"There are {val:.1f} maternal deaths for every 100,000 live births."

def _interpret_dsdr(val: float, ctx: Dict[str, Any]) -> str:
    std = ctx.get("standard_population_type", "standard")
    return f"Adjusted to the {std} population, the death rate is {val:.2f} per 1,000. This removes the effect of differing age structures."

def _interpret_smr(val: float, ctx: Dict[str, Any]) -> str:
    obs, exp = ctx.get("observed_deaths", 0), ctx.get("expected_deaths", 0)
    diff = (val - 1.0) * 100.0
    word = f"{abs(diff):.1f}% more deaths" if diff > 0 else f"{abs(diff):.1f}% fewer deaths"
    return f"Observed deaths ({obs:,.0f}) are {val:.3f} times the {exp:,.1f} expected at standard rates, which is {word} than expected."

def _interpret_isdr(val: float, ctx: Dict[str, Any]) -> str:
    return f"Using the indirect method, the age-adjusted death rate is {val:.2f} per 1,000."

def _interpret_e0(val: float, ctx: Dict[str, Any]) -> str:
    return f"A newborn can expect to live {val:.2f} years if today's age-specific death rates continue."

def _interpret_e65(val: float, ctx: Dict[str, Any]) -> str:
    return f"A person who reaches 65 can expect {val:.2f} more years of life, to about age {65.0 + val:.1f}."

def _interpret_45q15(val: float, ctx: Dict[str, Any]) -> str:
    pct = val * 100.0 if val <= 1.0 else val
    return f"A 15-year-old has a {pct:.2f}% chance of dying before age 60."

def _interpret_smam(val: float, ctx: Dict[str, Any]) -> str:
    who = {"male": "men", "female": "women"}.get(str(ctx.get("sex", "")).lower(), "people")
    return f"Among {who} who marry, the average age at first marriage is {val:.2f} years."

def _interpret_spousal_gap(val: float, ctx: Dict[str, Any]) -> str:
    return f"Husbands are on average {val:.2f} years older than their wives at first marriage."

def _interpret_celibacy(val: float, ctx: Dict[str, Any]) -> str:
    return f"{val:.2f}% of people reach age 50 without ever marrying."

def _interpret_cmrg(val: float, ctx: Dict[str, Any]) -> str:
    return f"There are {val:.2f} marriages per 1,000 people in the year."

def _interpret_cdvr(val: float, ctx: Dict[str, Any]) -> str:
    return f"There are {val:.2f} divorces per 1,000 people in the year."

def _interpret_gdvr(val: float, ctx: Dict[str, Any]) -> str:
    return f"There are {val:.2f} divorces per 1,000 married people."

def _interpret_nmrg(val: float, ctx: Dict[str, Any]) -> str:
    return f"The area {'gains' if val >= 0 else 'loses'} {abs(val):.2f} migrants per 1,000 people each year on balance."

def _interpret_mer(val: float, ctx: Dict[str, Any]) -> str:
    return f"Of every 100 moves, {abs(val):.2f} end up as a net shift of people. Values near 100 mean movement is mostly one-way."

def _interpret_lotka_r(val: float, ctx: Dict[str, Any]) -> str:
    verb = "grow" if val > 0.005 else ("shrink" if val < -0.005 else "stay about the same size")
    return f"If current fertility and mortality stayed fixed, the population would eventually {verb} at {val:+.2f}% a year."

def _interpret_intrinsic_b(val: float, ctx: Dict[str, Any]) -> str:
    return f"In the long run this population would have {val:.2f} births per 1,000 people each year."

def _interpret_intrinsic_d(val: float, ctx: Dict[str, Any]) -> str:
    return f"In the long run this population would have {val:.2f} deaths per 1,000 people each year."

def _interpret_gen_len(val: float, ctx: Dict[str, Any]) -> str:
    return f"A generation is {val:.2f} years: the average gap between a mother's birth and her daughter's."


MEASURES_CATALOGUE: Dict[str, Dict[str, Any]] = {
    # ------------------ S1: COMPOSITION & GROWTH ------------------
    "MP": {
        "code": "MP",
        "shortform": "MP",
        "full_name": "Masculinity Proportion",
        "display_name": "Masculinity Proportion (MP)",
        "block": "A: Sex Composition & Growth",
        "unit": "%",
        "formula": "MP = (Male Population / Total Population) * 100",
        "citation": "Shryock & Siegel (1976), Ch. 7; Bhende & Kanitkar (2010)",
        "interp_func": _interpret_mp,
    },
    "SR": {
        "code": "SR",
        "shortform": "SR",
        "full_name": "Sex Ratio",
        "display_name": "Sex Ratio (SR)",
        "block": "A: Sex Composition & Growth",
        "unit": "males per 100 females",
        "formula": "SR = (Male Population / Female Population) * 100",
        "citation": "UN Demographic Yearbook; Shryock & Siegel (1976)",
        "interp_func": _interpret_sr,
    },
    "SRB": {
        "code": "SRB",
        "shortform": "SRB",
        "full_name": "Sex Ratio at Birth",
        "display_name": "Sex Ratio at Birth (SRB)",
        "block": "A: Sex Composition & Growth",
        "unit": "male births per 100 female births",
        "formula": "SRB = (Male Live Births / Female Live Births) * 100",
        "citation": "Preston et al. (2001), Ch. 5; UN Population Division",
        "interp_func": _interpret_srb,
    },
    "EXCESS_M": {
        "code": "EXCESS_M",
        "shortform": "EXCESS_M",
        "full_name": "Excess of Males",
        "display_name": "Excess of Males (EXCESS_M)",
        "block": "A: Sex Composition & Growth",
        "unit": "persons",
        "formula": "Excess_M = Male Pop - Female Pop",
        "citation": "Bhende & Kanitkar (2010), Ch. 5",
        "interp_func": _interpret_excess_m,
    },
    "ACR": {
        "code": "ACR",
        "shortform": "ACR",
        "full_name": "Age Composition Ratio",
        "display_name": "Age Composition Ratio (ACR)",
        "block": "B: Age Structure & Dependency",
        "unit": "% working age",
        "formula": "ACR = (Pop 15-64 / Total Pop) * 100",
        "citation": "Rowland (2003), Ch. 3",
        "interp_func": _interpret_acr,
    },
    "TDR": {
        "code": "TDR",
        "shortform": "TDR",
        "full_name": "Total Dependency Ratio",
        "display_name": "Total Dependency Ratio (TDR)",
        "block": "B: Age Structure & Dependency",
        "unit": "dependents per 100 workers",
        "formula": "TDR = ((Pop 0-14 + Pop 65+) / Pop 15-64) * 100",
        "citation": "UN DESA Demographic Indicators; Rowland (2003)",
        "interp_func": _interpret_tdr,
    },
    "CDR_CHILD": {
        "code": "CDR_CHILD",
        "shortform": "CDR_CHILD",
        "full_name": "Child Dependency Ratio",
        "display_name": "Child Dependency Ratio (CDR_CHILD)",
        "block": "B: Age Structure & Dependency",
        "unit": "children per 100 workers",
        "formula": "CDR_child = (Pop 0-14 / Pop 15-64) * 100",
        "citation": "Bhende & Kanitkar (2010), Ch. 5",
        "interp_func": _interpret_cdr_child,
    },
    "OADR": {
        "code": "OADR",
        "shortform": "OADR",
        "full_name": "Old-Age Dependency Ratio",
        "display_name": "Old-Age Dependency Ratio (OADR)",
        "block": "B: Age Structure & Dependency",
        "unit": "seniors per 100 workers",
        "formula": "OADR = (Pop 65+ / Pop 15-64) * 100",
        "citation": "UN DESA Population Division; OECD Standards",
        "interp_func": _interpret_oadr,
    },
    "AI": {
        "code": "AI",
        "shortform": "AI",
        "full_name": "Ageing Index",
        "display_name": "Ageing Index (AI)",
        "block": "B: Age Structure & Dependency",
        "unit": "elderly per 100 children",
        "formula": "AI = (Pop 65+ / Pop 0-14) * 100",
        "citation": "Rowland (2003), Demographic Methods and Concepts",
        "interp_func": _interpret_ai,
    },
    "PSR": {
        "code": "PSR",
        "shortform": "PSR",
        "full_name": "Potential Support Ratio",
        "display_name": "Potential Support Ratio (PSR)",
        "block": "B: Age Structure & Dependency",
        "unit": "workers per elderly person",
        "formula": "PSR = Pop 15-64 / Pop 65+",
        "citation": "UN World Population Ageing; Preston et al. (2001)",
        "interp_func": _interpret_psr,
    },
    "MEDIAN_AGE": {
        "code": "MEDIAN_AGE",
        "shortform": "MA",
        "full_name": "Median Age",
        "display_name": "Median Age (MA)",
        "block": "B: Age Structure & Dependency",
        "unit": "years",
        "formula": "Linear interpolation of cumulative age distribution to 50%",
        "citation": "Shryock & Siegel (1976), Ch. 8",
        "interp_func": _interpret_median_age,
    },
    "CWR": {
        "code": "CWR",
        "shortform": "CWR",
        "full_name": "Child-Woman Ratio",
        "display_name": "Child-Woman Ratio (CWR)",
        "block": "B: Age Structure & Dependency",
        "unit": "children per 1,000 women 15-49",
        "formula": "CWR = (Pop 0-4 / Women 15-49) * 1000",
        "citation": "Bhende & Kanitkar (2010), Ch. 8",
        "interp_func": _interpret_cwr,
    },
    "DENSITY": {
        "code": "DENSITY",
        "shortform": "PD",
        "full_name": "Population Density",
        "display_name": "Population Density (PD)",
        "block": "B: Age Structure & Dependency",
        "unit": "persons per km²",
        "formula": "PD = Total Population / Area (km²)",
        "citation": "UN Population Division Standards",
        "interp_func": _interpret_density,
    },
    "GROWTH_RATE": {
        "code": "GROWTH_RATE",
        "shortform": "EGR",
        "full_name": "Exponential Growth Rate",
        "display_name": "Exponential Growth Rate (EGR)",
        "block": "B: Age Structure & Dependency",
        "unit": "% per year",
        "formula": "r = ln(P2 / P1) / t * 100",
        "citation": "Preston et al. (2001), Ch. 1",
        "interp_func": _interpret_growth_rate,
    },

    # ------------------ S3: FERTILITY ------------------
    "CBR": {
        "code": "CBR",
        "shortform": "CBR",
        "full_name": "Crude Birth Rate",
        "display_name": "Crude Birth Rate (CBR)",
        "block": "C: Fertility & Reproduction",
        "unit": "births per 1,000",
        "formula": "CBR = (Live Births / Total Population) * 1000",
        "citation": "Preston et al. (2001), Ch. 5",
        "interp_func": _interpret_cbr,
    },
    "GFR": {
        "code": "GFR",
        "shortform": "GFR",
        "full_name": "General Fertility Rate",
        "display_name": "General Fertility Rate (GFR)",
        "block": "C: Fertility & Reproduction",
        "unit": "births per 1,000 women (15-49)",
        "formula": "GFR = (Live Births / Women 15-49) * 1000",
        "citation": "Shryock & Siegel (1976), Ch. 16",
        "interp_func": _interpret_gfr,
    },
    "ASFR": {
        "code": "ASFR",
        "shortform": "ASFR",
        "full_name": "Age-Specific Fertility Rate",
        "display_name": "Age-Specific Fertility Rate (ASFR)",
        "block": "C: Fertility & Reproduction",
        "unit": "births per 1,000 women in age group",
        "formula": "ASFR_i = (Births_i / Women_i) * 1000",
        "citation": "Preston et al. (2001), Ch. 5",
        "interp_func": _interpret_asfr,
    },
    "TFR": {
        "code": "TFR",
        "shortform": "TFR",
        "full_name": "Total Fertility Rate",
        "display_name": "Total Fertility Rate (TFR)",
        "block": "C: Fertility & Reproduction",
        "unit": "children per woman",
        "formula": "TFR = 5 * sum(ASFR_i) / 1000",
        "citation": "UN Population Division Standards; Preston et al. (2001)",
        "interp_func": _interpret_tfr,
    },
    "GRR": {
        "code": "GRR",
        "shortform": "GRR",
        "full_name": "Gross Reproduction Rate",
        "display_name": "Gross Reproduction Rate (GRR)",
        "block": "C: Fertility & Reproduction",
        "unit": "daughters per woman",
        "formula": "GRR = TFR * (Female Births / Total Births)",
        "citation": "Preston et al. (2001), Ch. 5; Rowland (2003)",
        "interp_func": _interpret_grr,
    },
    "NRR": {
        "code": "NRR",
        "shortform": "NRR",
        "full_name": "Net Reproduction Rate",
        "display_name": "Net Reproduction Rate (NRR)",
        "block": "C: Fertility & Reproduction",
        "unit": "surviving daughters per woman",
        "formula": "NRR = sum( ASFR_f,i * (nLx / (n * l0)) )",
        "citation": "Preston et al. (2001), Ch. 5; Bhende & Kanitkar (2010)",
        "interp_func": _interpret_nrr,
    },
    "MBR": {
        "code": "MBR",
        "shortform": "GMFR",
        "full_name": "General Marital Fertility Rate",
        "display_name": "General Marital Fertility Rate (GMFR)",
        "block": "C: Fertility & Reproduction",
        "unit": "births per 1,000 married women (15-49)",
        "formula": "GMFR = (Marital Births / Married Women 15-49) * 1000",
        "citation": "Newell (1988), Ch. 4; Bhende & Kanitkar (2010)",
        "interp_func": _interpret_gmfr,
    },
    "MAC": {
        "code": "MAC",
        "shortform": "MAC",
        "full_name": "Mean Age at Childbearing",
        "display_name": "Mean Age at Childbearing (MAC)",
        "block": "C: Fertility & Reproduction",
        "unit": "years",
        "formula": "MAC = sum( (x + n/2) * ASFR_i ) / sum( ASFR_i )",
        "citation": "Preston et al. (2001), Ch. 5",
        "interp_func": _interpret_mac,
    },

    # ------------------ S4: MORTALITY ------------------
    "CDR": {
        "code": "CDR",
        "shortform": "CDR",
        "full_name": "Crude Death Rate",
        "display_name": "Crude Death Rate (CDR)",
        "block": "D: Mortality & Standardization",
        "unit": "deaths per 1,000",
        "formula": "CDR = (Total Deaths / Mid-Year Population) * 1000",
        "citation": "Preston et al. (2001), Ch. 2",
        "interp_func": _interpret_cdr,
    },
    "CORRECTED_CDR": {
        "code": "CORRECTED_CDR",
        "shortform": "CCDR",
        "full_name": "Corrected Crude Death Rate",
        "display_name": "Corrected Crude Death Rate (CCDR)",
        "block": "D: Mortality & Standardization",
        "unit": "adjusted deaths per 1,000",
        "formula": "CCDR = (Deaths / C_death) / (Pop / C_census) * 1000",
        "citation": "UN Principles and Recommendations; Chandra Sekar & Deming (1949)",
        "interp_func": _interpret_ccdr,
    },
    "NMR": {
        "code": "NMR",
        "shortform": "NMR",
        "full_name": "Neonatal Mortality Rate",
        "display_name": "Neonatal Mortality Rate (NMR)",
        "block": "D: Mortality & Standardization",
        "unit": "deaths per 1,000 live births",
        "formula": "NMR = (Deaths < 28 days / Live Births) * 1000",
        "citation": "WHO Global Health Observatory; SDG Target 3.2",
        "interp_func": _interpret_nmr,
    },
    "ENMR": {
        "code": "ENMR",
        "shortform": "ENMR",
        "full_name": "Early Neonatal Mortality Rate",
        "display_name": "Early Neonatal Mortality Rate (ENMR)",
        "block": "D: Mortality & Standardization",
        "unit": "deaths per 1,000 live births",
        "formula": "ENMR = (Deaths < 7 days / Live Births) * 1000",
        "citation": "WHO Guidelines; Preston et al. (2001)",
        "interp_func": _interpret_enmr,
    },
    "PNMR": {
        "code": "PNMR",
        "shortform": "PNMR",
        "full_name": "Post-Neonatal Mortality Rate",
        "display_name": "Post-Neonatal Mortality Rate (PNMR)",
        "block": "D: Mortality & Standardization",
        "unit": "deaths per 1,000 live births",
        "formula": "PNMR = ((Infant Deaths - Neonatal Deaths) / Live Births) * 1000",
        "citation": "WHO Child Mortality Guidelines",
        "interp_func": _interpret_pnmr,
    },
    "IMR": {
        "code": "IMR",
        "shortform": "IMR",
        "full_name": "Infant Mortality Rate",
        "display_name": "Infant Mortality Rate (IMR)",
        "block": "D: Mortality & Standardization",
        "unit": "deaths per 1,000 live births",
        "formula": "IMR = (Deaths < 1 year / Live Births) * 1000",
        "citation": "UNICEF / WHO; Preston et al. (2001), Ch. 2",
        "interp_func": _interpret_imr,
    },
    "CMR": {
        "code": "CMR",
        "shortform": "CDR(1-4)",
        "full_name": "Child Death Rate (Age 1-4)",
        "display_name": "Child Death Rate (CDR 1-4)",
        "block": "D: Mortality & Standardization",
        "unit": "deaths per 1,000 children (1-4)",
        "formula": "CDR(1-4) = (Deaths 1-4 / Population 1-4) * 1000",
        "citation": "Shryock & Siegel (1976), Ch. 14",
        "interp_func": _interpret_cdr_1_4,
    },
    "U5MR": {
        "code": "U5MR",
        "shortform": "U5MR",
        "full_name": "Under-5 Mortality Rate",
        "display_name": "Under-5 Mortality Rate (U5MR)",
        "block": "D: Mortality & Standardization",
        "unit": "deaths per 1,000 live births",
        "formula": "U5MR = (Deaths < 5 / Live Births) * 1000",
        "citation": "UN IGME Child Mortality Estimation; SDG Indicator 3.2.1",
        "interp_func": _interpret_u5mr,
    },
    "MMR": {
        "code": "MMR",
        "shortform": "MMR",
        "full_name": "Maternal Mortality Ratio",
        "display_name": "Maternal Mortality Ratio (MMR)",
        "block": "D: Mortality & Standardization",
        "unit": "deaths per 100,000 live births",
        "formula": "MMR = (Maternal Deaths / Live Births) * 100,000",
        "citation": "WHO / UNICEF / UNFPA Maternal Mortality Estimates",
        "interp_func": _interpret_mmr,
    },
    "ASDR": {
        "code": "ASDR",
        "shortform": "ASDR",
        "full_name": "Age-Specific Death Rate",
        "display_name": "Age-Specific Death Rate (ASDR)",
        "block": "D: Mortality & Standardization",
        "unit": "deaths per 1,000 in age group",
        "formula": "ASDR_i = (Deaths_i / Population_i) * 1000",
        "citation": "Preston et al. (2001), Ch. 2",
        "interp_func": lambda v, c: f"Age-specific mortality forms a characteristic U-curve, with minimum risk at age {c.get('lowest_mortality_age_group', '10-14')} ({c.get('lowest_mortality_rate', 0):.2f} per 1,000).",
    },
    "DSDR": {
        "code": "DSDR",
        "shortform": "DSDR",
        "full_name": "Direct Standardized Death Rate",
        "display_name": "Direct Standardized Death Rate (DSDR)",
        "block": "D: Mortality & Standardization",
        "unit": "standardized deaths per 1,000",
        "formula": "DSDR = sum( ASDR_i * P_std_i ) / sum( P_std_i )",
        "citation": "WHO Guidelines; Preston et al. (2001), Ch. 2",
        "interp_func": _interpret_dsdr,
    },
    "SMR": {
        "code": "SMR",
        "shortform": "SMR",
        "full_name": "Standardized Mortality Ratio",
        "display_name": "Standardized Mortality Ratio (SMR)",
        "block": "D: Mortality & Standardization",
        "unit": "ratio (Obs / Exp)",
        "formula": "SMR = Observed Deaths / Expected Deaths",
        "citation": "Breslow & Day (1987); Preston et al. (2001)",
        "interp_func": _interpret_smr,
    },
    "ISDR": {
        "code": "ISDR",
        "shortform": "ISDR",
        "full_name": "Indirect Standardized Death Rate",
        "display_name": "Indirect Standardized Death Rate (ISDR)",
        "block": "D: Mortality & Standardization",
        "unit": "deaths per 1,000",
        "formula": "ISDR = SMR * Standard CDR",
        "citation": "Shryock & Siegel (1976), Ch. 14",
        "interp_func": _interpret_isdr,
    },

    # ------------------ S5: LIFE TABLES ------------------
    "E0": {
        "code": "E0",
        "shortform": "e0",
        "full_name": "Life Expectancy at Birth",
        "display_name": "Life Expectancy at Birth (e0)",
        "block": "E: Life Tables",
        "unit": "years",
        "formula": "e0 = T0 / l0",
        "citation": "Preston et al. (2001), Ch. 3; Chiang (1984)",
        "interp_func": _interpret_e0,
    },
    "E65": {
        "code": "E65",
        "shortform": "e65",
        "full_name": "Life Expectancy at Age 65",
        "display_name": "Life Expectancy at Age 65 (e65)",
        "block": "E: Life Tables",
        "unit": "years remaining",
        "formula": "e65 = T65 / l65",
        "citation": "Preston et al. (2001), Ch. 3",
        "interp_func": _interpret_e65,
    },
    "45Q15": {
        "code": "45Q15",
        "shortform": "45q15",
        "full_name": "Adult Mortality Probability",
        "display_name": "Adult Mortality Probability (45q15)",
        "block": "E: Life Tables",
        "unit": "probability of dying (15-60)",
        "formula": "45q15 = 1 - (l60 / l15)",
        "citation": "UN Population Division; WHO Life Table Standards",
        "interp_func": _interpret_45q15,
    },

    # ------------------ S6: NUPTIALITY ------------------
    "SMAM_MALE": {
        "code": "SMAM_MALE",
        "shortform": "SMAM(M)",
        "full_name": "Singulate Mean Age at Marriage (Male)",
        "display_name": "Singulate Mean Age at Marriage — Male (SMAM-M)",
        "block": "F: Nuptiality & Marital Dynamics",
        "unit": "years",
        "formula": "Hajnal (1953) method on male single proportions 15-49",
        "citation": "Hajnal, J. (1953). Population Studies, 7(2):111-136",
        "interp_func": lambda v, c: _interpret_smam(v, {"sex": "male"}),
    },
    "SMAM_FEMALE": {
        "code": "SMAM_FEMALE",
        "shortform": "SMAM(F)",
        "full_name": "Singulate Mean Age at Marriage (Female)",
        "display_name": "Singulate Mean Age at Marriage — Female (SMAM-F)",
        "block": "F: Nuptiality & Marital Dynamics",
        "unit": "years",
        "formula": "Hajnal (1953) method on female single proportions 15-49",
        "citation": "Hajnal, J. (1953). Population Studies, 7(2):111-136",
        "interp_func": lambda v, c: _interpret_smam(v, {"sex": "female"}),
    },
    "SPOUSAL_GAP": {
        "code": "SPOUSAL_GAP",
        "shortform": "SAG",
        "full_name": "Spousal Age Gap",
        "display_name": "Spousal Age Gap (SAG)",
        "block": "F: Nuptiality & Marital Dynamics",
        "unit": "years",
        "formula": "SAG = SMAM(Male) - SMAM(Female)",
        "citation": "UN Demographic Guidelines; Bhende & Kanitkar (2010)",
        "interp_func": _interpret_spousal_gap,
    },
    "CELIBACY": {
        "code": "CELIBACY",
        "shortform": "CR",
        "full_name": "Definitive Celibacy Rate",
        "display_name": "Definitive Celibacy Rate (CR)",
        "block": "F: Nuptiality & Marital Dynamics",
        "unit": "% never married at 50",
        "formula": "CR = Proportion Never Married at Age 45-54 * 100",
        "citation": "Hajnal (1953); Rowland (2003)",
        "interp_func": _interpret_celibacy,
    },
    "CMRG": {
        "code": "CMRG",
        "shortform": "CMRg",
        "full_name": "Crude Marriage Rate",
        "display_name": "Crude Marriage Rate (CMRg)",
        "block": "F: Nuptiality & Marital Dynamics",
        "unit": "marriages per 1,000",
        "formula": "CMRg = (Marriages / Total Population) * 1000",
        "citation": "Shryock & Siegel (1976), Ch. 19",
        "interp_func": _interpret_cmrg,
    },
    "CDVR": {
        "code": "CDVR",
        "shortform": "CDvR",
        "full_name": "Crude Divorce Rate",
        "display_name": "Crude Divorce Rate (CDvR)",
        "block": "F: Nuptiality & Marital Dynamics",
        "unit": "divorces per 1,000",
        "formula": "CDvR = (Divorces / Total Population) * 1000",
        "citation": "Shryock & Siegel (1976), Ch. 19",
        "interp_func": _interpret_cdvr,
    },
    "GDVR": {
        "code": "GDVR",
        "shortform": "GDvR",
        "full_name": "General Divorce Rate",
        "display_name": "General Divorce Rate (GDvR)",
        "block": "F: Nuptiality & Marital Dynamics",
        "unit": "divorces per 1,000 married population",
        "formula": "GDvR = (Divorces / Married Population) * 1000",
        "citation": "Newell (1988); Bhende & Kanitkar (2010)",
        "interp_func": _interpret_gdvr,
    },

    # ------------------ S7: MIGRATION ------------------
    "NMRG": {
        "code": "NMRG",
        "shortform": "NMRg",
        "full_name": "Net Migration Rate",
        "display_name": "Net Migration Rate (NMRg)",
        "block": "G: Migration & Spatial Redistribution",
        "unit": "migrants per 1,000",
        "formula": "NMRg = ((In-Migrants - Out-Migrants) / Mid-Year Pop) * 1000",
        "citation": "UN Manual VI: Methods of Measuring Internal Migration",
        "interp_func": _interpret_nmrg,
    },
    "MER": {
        "code": "MER",
        "shortform": "MER",
        "full_name": "Migration Efficiency Ratio",
        "display_name": "Migration Efficiency Ratio (MER)",
        "block": "G: Migration & Spatial Redistribution",
        "unit": "%",
        "formula": "MER = ( |In - Out| / (In + Out) ) * 100",
        "citation": "Shryock & Siegel (1976), Ch. 21",
        "interp_func": _interpret_mer,
    },

    # ------------------ S9: STABLE POPULATION ------------------
    "LOTKA_R": {
        "code": "LOTKA_R",
        "shortform": "r_int",
        "full_name": "Intrinsic Rate of Natural Increase",
        "display_name": "Intrinsic Rate of Natural Increase (r_int)",
        "block": "H: Stable Population & Renewal",
        "unit": "% per year",
        "formula": "Root r of Lotka characteristic equation: sum( exp(-r * a) * f_f * nL / l0 ) = 1",
        "citation": "Lotka, A. J. (1939); Preston et al. (2001), Ch. 7",
        "interp_func": _interpret_lotka_r,
    },
    "INTRINSIC_B": {
        "code": "INTRINSIC_B",
        "shortform": "b_int",
        "full_name": "Intrinsic Birth Rate",
        "display_name": "Intrinsic Birth Rate (b_int)",
        "block": "H: Stable Population & Renewal",
        "unit": "births per 1,000",
        "formula": "b = 1 / sum( exp(-r * a) * nL / l0 )",
        "citation": "Preston et al. (2001), Ch. 7",
        "interp_func": _interpret_intrinsic_b,
    },
    "INTRINSIC_D": {
        "code": "INTRINSIC_D",
        "shortform": "d_int",
        "full_name": "Intrinsic Death Rate",
        "display_name": "Intrinsic Death Rate (d_int)",
        "block": "H: Stable Population & Renewal",
        "unit": "deaths per 1,000",
        "formula": "d = b - r",
        "citation": "Preston et al. (2001), Ch. 7",
        "interp_func": _interpret_intrinsic_d,
    },
    "GEN_LEN": {
        "code": "GEN_LEN",
        "shortform": "T",
        "full_name": "Mean Length of Generation",
        "display_name": "Mean Length of Generation (T)",
        "block": "H: Stable Population & Renewal",
        "unit": "years",
        "formula": "T = ln(NRR) / r",
        "citation": "Lotka (1939); Preston et al. (2001)",
        "interp_func": _interpret_gen_len,
    },
}


def get_measure_meta(code: str) -> Optional[Dict[str, Any]]:
    """Retrieve metadata entry for a given demographic measure code."""
    return MEASURES_CATALOGUE.get(code.upper())


def format_measure_name(code: str, fallback_name: str = "") -> str:
    """Returns 'Full Name (SHORTFORM)' ensuring standard display."""
    meta = get_measure_meta(code)
    if meta:
        return meta["display_name"]
    return fallback_name or code


def generate_measure_interpretation(code: str, value: float, context: Optional[Dict[str, Any]] = None) -> str:
    """Generates the plain demographic interpretation for a given measure code and value."""
    meta = get_measure_meta(code)
    ctx = context or {}
    if meta and "interp_func" in meta:
        try:
            return meta["interp_func"](value, ctx)
        except Exception:
            pass
    return f"Computed value is {value:.2f} {ctx.get('unit', '')}."


from engine import extra_measures as _extra_measures  # noqa: E402,F401  (registers the revision-sheet measures)
