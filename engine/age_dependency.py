"""
Block B / Section 1: Age Composition & Dependency Measures
Implements:
1. Age Composition Ratio (ACR)
2. Total Dependency Ratio (TDR)
3. Child Dependency Ratio (CDR_CHILD)
4. Old-Age Dependency Ratio (OADR)
5. Ageing Index (AI)
6. Potential Support Ratio (PSR)
7. Median Age (MA)
8. Child-Woman Ratio (CWR)
9. Population Density (PD)
10. Exponential Growth Rate (EGR) & Doubling Time

References:
- United Nations DESA Population Division (2022). World Population Prospects.
- Rowland, D. T. (2003). Demographic Methods and Concepts. Oxford University Press.
- Bhende, A., & Kanitkar, T. (2010). Principles of Population Studies, Ch. 5.
"""

from __future__ import annotations
import math
from typing import Dict, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
from engine.base import DemographicMeasureResult, DemographicDataset
from engine.registry import format_measure_name, generate_measure_interpretation


def calculate_age_composition_ratio(
    pop_0_14: float,
    pop_15_64: float,
    pop_65_plus: float,
    total_population: Optional[float] = None,
) -> DemographicMeasureResult:
    """Calculate Age Composition Ratio (ACR)."""
    if total_population is None:
        total_population = pop_0_14 + pop_15_64 + pop_65_plus
        
    if total_population <= 0:
        raise ValueError("Total population must be strictly positive.")
        
    pct_0_14 = (pop_0_14 / total_population) * 100.0
    pct_15_64 = (pop_15_64 / total_population) * 100.0
    pct_65_plus = (pop_65_plus / total_population) * 100.0
    
    inputs = {
        "pop_0_14": pop_0_14,
        "pop_15_64": pop_15_64,
        "pop_65_plus": pop_65_plus,
        "total_population": total_population,
        "pct_0_14": pct_0_14,
        "pct_15_64": pct_15_64,
        "pct_65_plus": pct_65_plus,
    }
    plain_interp = generate_measure_interpretation("ACR", pct_15_64, inputs)
    
    return DemographicMeasureResult(
        code="ACR",
        shortform="ACR",
        full_name="Age Composition Ratio",
        name=format_measure_name("ACR", "Age Composition Ratio (ACR)"),
        block="B: Age Structure & Dependency",
        raw_value=pct_15_64,
        formatted_value=f"Working: {pct_15_64:.1f}% | Youth: {pct_0_14:.1f}% | Elderly: {pct_65_plus:.1f}%",
        unit="%",
        formula="ACR_i = (Population in Age Bracket i / Total Population) * 100",
        citation="Rowland (2003), Demographic Methods and Concepts, Ch. 3",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="A working-age share > 60-65% indicates an expansive demographic dividend window."
    )


def calculate_total_dependency_ratio(
    pop_0_14: float,
    pop_15_64: float,
    pop_65_plus: float,
    per: int = 100,
) -> DemographicMeasureResult:
    """Calculate Total Dependency Ratio (TDR)."""
    if pop_15_64 <= 0:
        raise ValueError("Working-age population (15-64) must be strictly positive.")
        
    tdr_val = ((pop_0_14 + pop_65_plus) / pop_15_64) * float(per)
    inputs = {
        "pop_0_14": pop_0_14,
        "pop_15_64": pop_15_64,
        "pop_65_plus": pop_65_plus,
        "per": per,
    }
    plain_interp = generate_measure_interpretation("TDR", tdr_val, inputs)
    
    return DemographicMeasureResult(
        code="TDR",
        shortform="TDR",
        full_name="Total Dependency Ratio",
        name=format_measure_name("TDR", "Total Dependency Ratio (TDR)"),
        block="B: Age Structure & Dependency",
        raw_value=tdr_val,
        formatted_value=f"{tdr_val:.2f} dependents per {per} working-age persons",
        unit=f"per {per} working-age",
        formula=f"TDR = ((P_0_14 + P_65+) / P_15_64) * {per}",
        citation="UN DESA Demographic Indicators; Rowland (2003), Ch. 3",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="Global benchmark: < 50 indicates high economic bonus window; > 70 indicates high dependency burden."
    )


def calculate_child_dependency_ratio(
    pop_0_14: float,
    pop_15_64: float,
    per: int = 100,
) -> DemographicMeasureResult:
    """Calculate Child Dependency Ratio (CDR_CHILD)."""
    if pop_15_64 <= 0:
        raise ValueError("Working-age population (15-64) must be strictly positive.")
        
    cdr_child_val = (pop_0_14 / pop_15_64) * float(per)
    inputs = {
        "pop_0_14": pop_0_14,
        "pop_15_64": pop_15_64,
        "per": per,
    }
    plain_interp = generate_measure_interpretation("CDR_CHILD", cdr_child_val, inputs)
    
    return DemographicMeasureResult(
        code="CDR_CHILD",
        shortform="CDR_CHILD",
        full_name="Child Dependency Ratio",
        name=format_measure_name("CDR_CHILD", "Child Dependency Ratio (CDR_CHILD)"),
        block="B: Age Structure & Dependency",
        raw_value=cdr_child_val,
        formatted_value=f"{cdr_child_val:.2f} children per {per} working-age persons",
        unit=f"per {per} working-age",
        formula=f"CDR_child = (P_0_14 / P_15_64) * {per}",
        citation="Bhende & Kanitkar (2010), Principles of Population Studies, Ch. 5",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="High child dependency (> 45) reflects youthful fertility requiring educational investment."
    )


def calculate_old_age_dependency_ratio(
    pop_65_plus: float,
    pop_15_64: float,
    per: int = 100,
) -> DemographicMeasureResult:
    """Calculate Old-Age Dependency Ratio (OADR)."""
    if pop_15_64 <= 0:
        raise ValueError("Working-age population (15-64) must be strictly positive.")
        
    oadr_val = (pop_65_plus / pop_15_64) * float(per)
    inputs = {
        "pop_65_plus": pop_65_plus,
        "pop_15_64": pop_15_64,
        "per": per,
    }
    plain_interp = generate_measure_interpretation("OADR", oadr_val, inputs)
    
    return DemographicMeasureResult(
        code="OADR",
        shortform="OADR",
        full_name="Old-Age Dependency Ratio",
        name=format_measure_name("OADR", "Old-Age Dependency Ratio (OADR)"),
        block="B: Age Structure & Dependency",
        raw_value=oadr_val,
        formatted_value=f"{oadr_val:.2f} elderly per {per} working-age persons",
        unit=f"per {per} working-age",
        formula=f"OADR = (P_65+ / P_15_64) * {per}",
        citation="UN DESA Population Division; Rowland (2003), Ch. 3",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="Values > 20 indicate rapid population aging, placing pressure on pension and healthcare systems."
    )


def calculate_ageing_index(
    pop_0_14: float,
    pop_65_plus: float,
) -> DemographicMeasureResult:
    """Calculate Ageing Index (AI): (Pop 65+ / Pop 0-14) * 100."""
    if pop_0_14 <= 0:
        raise ValueError("Youth population (0-14) must be strictly positive.")
    ai_val = (pop_65_plus / pop_0_14) * 100.0
    inputs = {"pop_0_14": pop_0_14, "pop_65_plus": pop_65_plus}
    plain_interp = generate_measure_interpretation("AI", ai_val, inputs)
    
    return DemographicMeasureResult(
        code="AI",
        shortform="AI",
        full_name="Ageing Index",
        name=format_measure_name("AI", "Ageing Index (AI)"),
        block="B: Age Structure & Dependency",
        raw_value=ai_val,
        formatted_value=f"{ai_val:.1f} elderly per 100 children",
        unit="elderly per 100 children",
        formula="AI = (Pop 65+ / Pop 0-14) * 100",
        citation="Rowland (2003), Demographic Methods and Concepts, Ch. 3",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
    )


def calculate_potential_support_ratio(
    pop_15_64: float,
    pop_65_plus: float,
) -> DemographicMeasureResult:
    """Calculate Potential Support Ratio (PSR): Pop 15-64 / Pop 65+."""
    if pop_65_plus <= 0:
        raise ValueError("Elderly population (65+) must be strictly positive.")
    psr_val = pop_15_64 / pop_65_plus
    inputs = {"pop_15_64": pop_15_64, "pop_65_plus": pop_65_plus}
    plain_interp = generate_measure_interpretation("PSR", psr_val, inputs)
    
    return DemographicMeasureResult(
        code="PSR",
        shortform="PSR",
        full_name="Potential Support Ratio",
        name=format_measure_name("PSR", "Potential Support Ratio (PSR)"),
        block="B: Age Structure & Dependency",
        raw_value=psr_val,
        formatted_value=f"{psr_val:.1f} workers per senior",
        unit="workers per senior",
        formula="PSR = Pop 15-64 / Pop 65+",
        citation="UN Population Division, World Population Ageing",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
    )


def calculate_median_age(single_or_5yr_df: pd.DataFrame) -> DemographicMeasureResult:
    """Calculates Median Age by interpolating the 50th percentile of cumulative population."""
    df = single_or_5yr_df.copy()
    tot_col = "total" if "total" in df.columns else ("male" if "male" in df.columns else df.columns[-1])
    if "total" not in df.columns and "male" in df.columns and "female" in df.columns:
        df["total"] = df["male"] + df["female"]
        tot_col = "total"
        
    tot_pop = df[tot_col].sum()
    half_pop = tot_pop / 2.0
    
    med_age = 28.0 # fallback
    if "age" in df.columns:
        # single year
        df = df.sort_values("age")
        df["cum"] = df[tot_col].cumsum()
        idx = df[df["cum"] >= half_pop].index
        if len(idx) > 0:
            row = df.loc[idx[0]]
            prev_cum = df.loc[idx[0] - 1]["cum"] if idx[0] > df.index[0] else 0.0
            cur_pop = row[tot_col]
            med_age = float(row["age"]) + ((half_pop - prev_cum) / cur_pop if cur_pop > 0 else 0.0)
    else:
        # 5 year age groups
        cum = 0.0
        for _, r in df.iterrows():
            pop = float(r[tot_col])
            lbl = str(r["age_group"])
            parts = lbl.replace("+", "").split("-")
            low = float(parts[0])
            width = float(parts[1]) - low + 1.0 if len(parts) > 1 else 15.0
            if cum + pop >= half_pop:
                med_age = low + ((half_pop - cum) / pop) * width
                break
            cum += pop
            
    inputs = {"median_age": med_age, "total_population": tot_pop}
    plain_interp = generate_measure_interpretation("MEDIAN_AGE", med_age, inputs)
    
    return DemographicMeasureResult(
        code="MEDIAN_AGE",
        shortform="MA",
        full_name="Median Age",
        name=format_measure_name("MEDIAN_AGE", "Median Age (MA)"),
        block="B: Age Structure & Dependency",
        raw_value=med_age,
        formatted_value=f"{med_age:.1f} years",
        unit="years",
        formula="Linear interpolation of cumulative age distribution to 50%",
        citation="Shryock & Siegel (1976), The Methods and Materials of Demography, Ch. 8",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
    )


def calculate_child_woman_ratio(pop_0_4: float, women_15_49: float) -> DemographicMeasureResult:
    """Calculate Child-Woman Ratio (CWR): (Pop 0-4 / Women 15-49) * 1000."""
    if women_15_49 <= 0:
        raise ValueError("Women 15-49 must be strictly positive.")
    cwr_val = (pop_0_4 / women_15_49) * 1000.0
    inputs = {"pop_0_4": pop_0_4, "women_15_49": women_15_49}
    plain_interp = generate_measure_interpretation("CWR", cwr_val, inputs)
    
    return DemographicMeasureResult(
        code="CWR",
        shortform="CWR",
        full_name="Child-Woman Ratio",
        name=format_measure_name("CWR", "Child-Woman Ratio (CWR)"),
        block="B: Age Structure & Dependency",
        raw_value=cwr_val,
        formatted_value=f"{cwr_val:.1f} children per 1,000 women (15-49)",
        unit="per 1,000 women (15-49)",
        formula="CWR = (Pop 0-4 / Women 15-49) * 1000",
        citation="Bhende & Kanitkar (2010), Principles of Population Studies, Ch. 8",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
    )


def calculate_population_density(total_population: float, area_km2: float) -> DemographicMeasureResult:
    """Calculate Population Density (PD): Total Population / Area km2."""
    if area_km2 <= 0:
        raise ValueError("Area must be strictly positive.")
    dens_val = total_population / area_km2
    inputs = {"total_population": total_population, "area_km2": area_km2}
    plain_interp = generate_measure_interpretation("DENSITY", dens_val, inputs)
    
    return DemographicMeasureResult(
        code="DENSITY",
        shortform="PD",
        full_name="Population Density",
        name=format_measure_name("DENSITY", "Population Density (PD)"),
        block="B: Age Structure & Dependency",
        raw_value=dens_val,
        formatted_value=f"{dens_val:,.1f} persons/km²",
        unit="persons/km²",
        formula="PD = Total Population / Area (km²)",
        citation="UN Population Division Standards",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
    )


def calculate_growth_rate(
    current_pop: float,
    previous_pop: float,
    years: float,
) -> DemographicMeasureResult:
    """Calculate Exponential Growth Rate (r) and Doubling Time."""
    if current_pop <= 0 or previous_pop <= 0 or years <= 0:
        raise ValueError("Populations and elapsed years must be strictly positive.")
    r_val = (math.log(current_pop / previous_pop) / years) * 100.0
    dt_val = (math.log(2) / (r_val / 100.0)) if r_val > 0 else None
    
    inputs = {
        "current_pop": current_pop,
        "previous_pop": previous_pop,
        "years": years,
        "doubling_time": dt_val,
    }
    plain_interp = generate_measure_interpretation("GROWTH_RATE", r_val, inputs)
    dt_str = f" (Doubling time: {dt_val:.1f} yrs)" if dt_val else ""
    
    return DemographicMeasureResult(
        code="GROWTH_RATE",
        shortform="EGR",
        full_name="Exponential Growth Rate",
        name=format_measure_name("GROWTH_RATE", "Exponential Growth Rate (EGR)"),
        block="B: Age Structure & Dependency",
        raw_value=r_val,
        formatted_value=f"{r_val:.2f}% per year{dt_str}",
        unit="% per year",
        formula="r = (ln(P_t2 / P_t1) / t) * 100; Doubling Time = ln(2) / r",
        citation="Preston et al. (2001), Demography, Ch. 1",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
    )


def extract_broad_age_groups_from_tables(dataset: DemographicDataset) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Helper to extract or derive (0-14, 15-64, 65+) from 5-year or single-year age tables."""
    p_0_14 = dataset.pop_0_14
    p_15_64 = dataset.pop_15_64
    p_65_plus = dataset.pop_65_plus
    
    if (p_0_14 is not None) and (p_15_64 is not None) and (p_65_plus is not None):
        return p_0_14, p_15_64, p_65_plus
        
    if dataset.age_group_5yr is not None:
        df = dataset.age_group_5yr.copy()
        tot_col = "total" if "total" in df.columns else ("male" if "male" in df.columns else df.columns[1])
        if "male" in df.columns and "female" in df.columns and "total" not in df.columns:
            df["total"] = df["male"] + df["female"]
            tot_col = "total"
            
        young_groups = ["0-4", "5-9", "10-14"]
        work_groups = ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64"]
        old_groups = ["65-69", "70-74", "75-79", "80-84", "85+", "80+"]
        
        y_sum = df[df["age_group"].isin(young_groups)][tot_col].sum()
        w_sum = df[df["age_group"].isin(work_groups)][tot_col].sum()
        o_sum = df[df["age_group"].isin(old_groups)][tot_col].sum()
        
        if y_sum > 0 and w_sum > 0:
            return float(y_sum), float(w_sum), float(o_sum)
            
    if dataset.single_year_ages is not None:
        df = dataset.single_year_ages.copy()
        tot_col = "total" if "total" in df.columns else ("male" if "male" in df.columns else df.columns[1])
        if "male" in df.columns and "female" in df.columns and "total" not in df.columns:
            df["total"] = df["male"] + df["female"]
            tot_col = "total"
            
        y_sum = df[(df["age"] >= 0) & (df["age"] <= 14)][tot_col].sum()
        w_sum = df[(df["age"] >= 15) & (df["age"] <= 64)][tot_col].sum()
        o_sum = df[df["age"] >= 65][tot_col].sum()
        
        if y_sum > 0 and w_sum > 0:
            return float(y_sum), float(w_sum), float(o_sum)
            
    return p_0_14, p_15_64, p_65_plus


def _compute_block_b_core(dataset: DemographicDataset) -> Dict[str, DemographicMeasureResult]:
    """Compute all Block B age & dependency measures from a demographic dataset."""
    results: Dict[str, DemographicMeasureResult] = {}
    
    p_0_14, p_15_64, p_65_plus = extract_broad_age_groups_from_tables(dataset)
    t_pop = dataset.total_population
    if t_pop is None and p_0_14 is not None and p_15_64 is not None and p_65_plus is not None:
        t_pop = p_0_14 + p_15_64 + p_65_plus
        
    if p_0_14 is not None and p_15_64 is not None and p_65_plus is not None:
        results["ACR"] = calculate_age_composition_ratio(p_0_14, p_15_64, p_65_plus, t_pop)
        results["TDR"] = calculate_total_dependency_ratio(p_0_14, p_15_64, p_65_plus)
        results["CDR_CHILD"] = calculate_child_dependency_ratio(p_0_14, p_15_64)
        results["OADR"] = calculate_old_age_dependency_ratio(p_65_plus, p_15_64)
        
        if p_0_14 > 0:
            results["AI"] = calculate_ageing_index(p_0_14, p_65_plus)
        if p_65_plus > 0:
            results["PSR"] = calculate_potential_support_ratio(p_15_64, p_65_plus)
            
    # Median age if age distribution available
    if dataset.single_year_ages is not None and not dataset.single_year_ages.empty:
        results["MEDIAN_AGE"] = calculate_median_age(dataset.single_year_ages)
    elif dataset.age_group_5yr is not None and not dataset.age_group_5yr.empty:
        results["MEDIAN_AGE"] = calculate_median_age(dataset.age_group_5yr)
        
    # Child-woman ratio if pop 0-4 and women 15-49 available
    pop_0_4 = None
    if dataset.age_group_5yr is not None:
        r04 = dataset.age_group_5yr[dataset.age_group_5yr["age_group"].isin(["0-4", "0 to 4"])]
        if not r04.empty:
            pop_0_4 = float(r04["total"].values[0])
    elif dataset.single_year_ages is not None:
        pop_0_4 = float(dataset.single_year_ages[dataset.single_year_ages["age"] <= 4]["total"].sum())
        
    w_15_49 = dataset.total_women_15_49
    if w_15_49 is None and dataset.fertility_schedule is not None and "female_pop" in dataset.fertility_schedule.columns:
        w_15_49 = float(dataset.fertility_schedule["female_pop"].sum())
        
    if pop_0_4 is not None and w_15_49 is not None and w_15_49 > 0:
        results["CWR"] = calculate_child_woman_ratio(pop_0_4, w_15_49)
        
    # Population density if area provided
    if t_pop is not None and dataset.area_km2 is not None and dataset.area_km2 > 0:
        results["DENSITY"] = calculate_population_density(t_pop, dataset.area_km2)
        
    # Growth rate if previous census data provided
    if t_pop is not None and dataset.previous_census_pop is not None and dataset.previous_census_year and dataset.year:
        elapsed = dataset.year - dataset.previous_census_year
        if elapsed > 0:
            results["GROWTH_RATE"] = calculate_growth_rate(t_pop, dataset.previous_census_pop, float(elapsed))
            
    return results


def compute_block_b(dataset: DemographicDataset) -> Dict[str, DemographicMeasureResult]:
    """Core measures plus the additional measures from the class revision sheet."""
    from engine import extra_measures as _xm
    results = _compute_block_b_core(dataset)
    for k, v in _xm.compute_composition_extras(dataset).items():
        results.setdefault(k, v)
    return results
