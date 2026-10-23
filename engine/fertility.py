"""
Block C / Section 3: Fertility & Reproduction Measures
Implements:
1. Crude Birth Rate (CBR)
2. General Marital Fertility Rate (GMFR / MBR)
3. General Fertility Rate (GFR)
4. Age-Specific Fertility Rate (ASFR)
5. Total Fertility Rate (TFR)
6. Gross Reproduction Rate (GRR)
7. Net Reproduction Rate (NRR) (Integrated with Life Table nLx)
8. Mean Age at Childbearing (MAC)
9. Bongaarts Proximate Determinants model (Quantitative link: Fecundity vs Fertility)

References:
- Preston, S. H., Heuveline, P., & Guillot, M. (2001). Demography: Measuring and Modeling Population Processes. Blackwell.
- Newell, C. (1988). Methods and Models in Demography. Guilford Press.
- Bhende, A., & Kanitkar, T. (2010). Principles of Population Studies, Ch. 8.
- Bongaarts, J. (1978). A framework for analyzing the proximate determinants of fertility.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple, Union
import numpy as np
import pandas as pd

from engine.base import DemographicMeasureResult, DemographicDataset
from engine.registry import format_measure_name, generate_measure_interpretation
from engine.lifetable import build_abridged_life_table


def calculate_crude_birth_rate(
    total_live_births: float,
    total_population: float,
    per: int = 1000,
) -> DemographicMeasureResult:
    """Calculate Crude Birth Rate (CBR)."""
    if total_population <= 0:
        raise ValueError("Total population must be strictly positive.")
    if total_live_births < 0:
        raise ValueError("Live births cannot be negative.")
        
    cbr_val = (total_live_births / total_population) * float(per)
    inputs = {
        "total_live_births": total_live_births,
        "total_population": total_population,
        "per": per,
    }
    plain_interp = generate_measure_interpretation("CBR", cbr_val, inputs)
    
    return DemographicMeasureResult(
        code="CBR",
        shortform="CBR",
        full_name="Crude Birth Rate",
        name=format_measure_name("CBR", "Crude Birth Rate (CBR)"),
        block="C: Fertility & Reproduction",
        raw_value=cbr_val,
        formatted_value=f"{cbr_val:.2f} births per {per:,} population",
        unit=f"births per {per:,}",
        formula=f"CBR = (Total Live Births / Total Mid-Year Population) * {per}",
        citation="Preston et al. (2001), Demography, Ch. 5",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="Global benchmark: < 15 is low (developed), 15-25 is moderate, > 25 is high fertility."
    )


def calculate_marital_birth_rate(
    marital_live_births: Optional[float],
    married_women_15_49: Optional[float],
    per: int = 1000,
) -> DemographicMeasureResult:
    """Calculate General Marital Fertility Rate (GMFR / MBR)."""
    if marital_live_births is None:
        raise ValueError("Marital live births must be explicitly provided (cannot be None).")
    if married_women_15_49 is None or married_women_15_49 <= 0:
        raise ValueError("Married women (15-49) must be strictly positive.")
    if marital_live_births < 0:
        raise ValueError("Marital live births cannot be negative.")
        
    mbr_val = (marital_live_births / married_women_15_49) * float(per)
    inputs = {
        "marital_live_births": marital_live_births,
        "married_women_15_49": married_women_15_49,
        "per": per,
    }
    plain_interp = generate_measure_interpretation("MBR", mbr_val, inputs)
    
    return DemographicMeasureResult(
        code="MBR",
        shortform="GMFR",
        full_name="General Marital Fertility Rate",
        name=format_measure_name("MBR", "General Marital Fertility Rate (GMFR)"),
        block="C: Fertility & Reproduction",
        raw_value=mbr_val,
        formatted_value=f"{mbr_val:.2f} births per {per:,} married women (15-49)",
        unit=f"births per {per:,} married women",
        formula=f"GMFR = (Marital Live Births / Married Women 15-49) * {per}",
        citation="Newell (1988), Methods and Models in Demography, Ch. 4; Bhende & Kanitkar (2010)",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="Measures fertility pressure strictly within marriage independently of marital status distribution."
    )


def calculate_general_fertility_rate(
    total_live_births: float,
    total_women_15_49: float,
    per: int = 1000,
) -> DemographicMeasureResult:
    """Calculate General Fertility Rate (GFR)."""
    if total_women_15_49 <= 0:
        raise ValueError("Women of reproductive age (15-49) must be strictly positive.")
    if total_live_births < 0:
        raise ValueError("Live births cannot be negative.")
        
    gfr_val = (total_live_births / total_women_15_49) * float(per)
    inputs = {
        "total_live_births": total_live_births,
        "total_women_15_49": total_women_15_49,
        "per": per,
    }
    plain_interp = generate_measure_interpretation("GFR", gfr_val, inputs)
    
    return DemographicMeasureResult(
        code="GFR",
        shortform="GFR",
        full_name="General Fertility Rate",
        name=format_measure_name("GFR", "General Fertility Rate (GFR)"),
        block="C: Fertility & Reproduction",
        raw_value=gfr_val,
        formatted_value=f"{gfr_val:.2f} births per {per:,} women (15-49)",
        unit=f"births per {per:,} women (15-49)",
        formula=f"GFR = (Total Live Births / Total Women 15-49) * {per}",
        citation="Shryock & Siegel (1976), Ch. 16; Preston et al. (2001)",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="Refines CBR by restricting the denominator strictly to women in the reproductive age span."
    )


def calculate_age_specific_fertility_rates(
    fertility_schedule: pd.DataFrame,
    per: int = 1000,
) -> Tuple[DemographicMeasureResult, pd.DataFrame]:
    """Calculate Age-Specific Fertility Rates (ASFR)."""
    df = fertility_schedule.copy()
    if "female_pop" not in df.columns or "births" not in df.columns:
        raise ValueError("fertility_schedule must contain 'female_pop' and 'births' columns.")
        
    df["asfr"] = (df["births"] / df["female_pop"]) * float(per)
    peak_row = df.loc[df["asfr"].idxmax()] if not df.empty else None
    peak_age = peak_row["age_group"] if peak_row is not None else "N/A"
    peak_val = peak_row["asfr"] if peak_row is not None else 0.0
    
    asfr_dict = dict(zip(df["age_group"], df["asfr"]))
    mean_asfr = float(df["asfr"].mean())
    
    inputs = {
        "asfr_schedule": asfr_dict,
        "peak_age_group": peak_age,
        "peak_asfr": peak_val,
        "mean_asfr": mean_asfr,
    }
    plain_interp = generate_measure_interpretation("ASFR", peak_val, inputs)
    
    res = DemographicMeasureResult(
        code="ASFR",
        shortform="ASFR",
        full_name="Age-Specific Fertility Rate",
        name=format_measure_name("ASFR", "Age-Specific Fertility Rate (ASFR)"),
        block="C: Fertility & Reproduction",
        raw_value=peak_val,
        formatted_value=f"Peak: {peak_val:.1f} per {per:,} (Age {peak_age})",
        unit=f"births per {per:,} women in age group",
        formula=f"ASFR_i = (Births_i / Women_i) * {per}",
        citation="Preston et al. (2001), Ch. 5; Newell (1988), Ch. 4",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="Reveals the maternal age pattern of childbearing; peak is typically in the 20-24 or 25-29 age bracket."
    )
    return res, df


def calculate_mean_age_at_childbearing(fertility_schedule: pd.DataFrame) -> DemographicMeasureResult:
    """Calculate Mean Age at Childbearing (MAC)."""
    df = fertility_schedule.copy()
    if "asfr" not in df.columns:
        df["asfr"] = (df["births"] / df["female_pop"]) * 1000.0
        
    midpoints = []
    for lbl in df["age_group"]:
        parts = str(lbl).split("-")
        low = float(parts[0])
        high = float(parts[1]) if len(parts) > 1 else low + 4.0
        midpoints.append((low + high + 1.0) / 2.0)
        
    df["mid"] = midpoints
    sum_fx = df["asfr"].sum()
    if sum_fx <= 0:
        mac_val = 28.0
    else:
        mac_val = (df["mid"] * df["asfr"]).sum() / sum_fx
        
    inputs = {"mac": mac_val, "sum_asfr": sum_fx}
    plain_interp = generate_measure_interpretation("MAC", mac_val, inputs)
    
    return DemographicMeasureResult(
        code="MAC",
        shortform="MAC",
        full_name="Mean Age at Childbearing",
        name=format_measure_name("MAC", "Mean Age at Childbearing (MAC)"),
        block="C: Fertility & Reproduction",
        raw_value=mac_val,
        formatted_value=f"{mac_val:.1f} years",
        unit="years",
        formula="MAC = sum( (x + n/2) * ASFR_i ) / sum( ASFR_i )",
        citation="Preston et al. (2001), Ch. 5",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
    )


def calculate_total_fertility_rate(
    fertility_schedule_or_asfrs: Union[pd.DataFrame, List[float], Dict[str, float]],
    age_interval: int = 5,
) -> DemographicMeasureResult:
    """Calculate Total Fertility Rate (TFR)."""
    if isinstance(fertility_schedule_or_asfrs, pd.DataFrame):
        df = fertility_schedule_or_asfrs
        if "asfr" in df.columns:
            sum_asfr = df["asfr"].sum()
        elif "births" in df.columns and "female_pop" in df.columns:
            sum_asfr = (df["births"] / df["female_pop"] * 1000.0).sum()
        else:
            raise ValueError("DataFrame must contain 'asfr' or ('births' and 'female_pop').")
        tfr_val = (age_interval * sum_asfr) / 1000.0
    elif isinstance(fertility_schedule_or_asfrs, dict):
        sum_asfr = sum(fertility_schedule_or_asfrs.values())
        tfr_val = (age_interval * sum_asfr) / 1000.0
    elif isinstance(fertility_schedule_or_asfrs, (list, np.ndarray)):
        sum_asfr = sum(fertility_schedule_or_asfrs)
        tfr_val = (age_interval * sum_asfr) / 1000.0
    else:
        raise TypeError("Unsupported format for fertility schedule.")
        
    inputs = {
        "sum_asfr": sum_asfr,
        "age_interval": age_interval,
        "tfr": tfr_val,
    }
    plain_interp = generate_measure_interpretation("TFR", tfr_val, inputs)
    
    return DemographicMeasureResult(
        code="TFR",
        shortform="TFR",
        full_name="Total Fertility Rate",
        name=format_measure_name("TFR", "Total Fertility Rate (TFR)"),
        block="C: Fertility & Reproduction",
        raw_value=tfr_val,
        formatted_value=f"{tfr_val:.2f} children per woman",
        unit="children per woman",
        formula=f"TFR = {age_interval} * sum(ASFR_i) / 1000",
        citation="Preston et al. (2001), Ch. 5; UN DESA Population Division",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="Replacement-level fertility in low-mortality populations is ~2.1 children per woman."
    )


def calculate_gross_reproduction_rate(
    tfr: Optional[float] = None,
    fertility_schedule: Optional[pd.DataFrame] = None,
    female_birth_proportion: float = 100.0 / 205.0,  # ~0.4878 (SRB ~ 105 M : 100 F)
    age_interval: int = 5,
) -> DemographicMeasureResult:
    """Calculate Gross Reproduction Rate (GRR)."""
    if fertility_schedule is not None and "female_births" in fertility_schedule.columns and "female_pop" in fertility_schedule.columns:
        sum_f_asfr = (fertility_schedule["female_births"] / fertility_schedule["female_pop"] * 1000.0).sum()
        grr_val = (age_interval * sum_f_asfr) / 1000.0
    elif tfr is not None:
        grr_val = tfr * female_birth_proportion
    elif fertility_schedule is not None and "births" in fertility_schedule.columns and "female_pop" in fertility_schedule.columns:
        tfr_res = calculate_total_fertility_rate(fertility_schedule, age_interval)
        grr_val = tfr_res.raw_value * female_birth_proportion
    else:
        raise ValueError("Either TFR or a valid fertility_schedule must be provided.")
        
    inputs = {
        "tfr": tfr,
        "female_birth_proportion": female_birth_proportion,
        "age_interval": age_interval,
        "grr": grr_val,
    }
    plain_interp = generate_measure_interpretation("GRR", grr_val, inputs)
    
    return DemographicMeasureResult(
        code="GRR",
        shortform="GRR",
        full_name="Gross Reproduction Rate",
        name=format_measure_name("GRR", "Gross Reproduction Rate (GRR)"),
        block="C: Fertility & Reproduction",
        raw_value=grr_val,
        formatted_value=f"{grr_val:.3f} daughters per woman",
        unit="daughters per woman",
        formula="GRR = TFR * (Female Births / Total Births) [or 5 * sum(ASFR_female) / 1000]",
        citation="Preston et al. (2001), Ch. 5; Rowland (2003), Ch. 7",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="Average number of daughters born per woman if she survives the entire reproductive span."
    )


def calculate_net_reproduction_rate(
    grr: Optional[float] = None,
    tfr: Optional[float] = None,
    fertility_schedule: Optional[pd.DataFrame] = None,
    life_table_female: Optional[pd.DataFrame] = None,
    mortality_schedule: Optional[pd.DataFrame] = None,
    female_survival_to_childbearing: float = 0.965,
    female_birth_proportion: float = 100.0 / 205.0,
    age_interval: int = 5,
    radix: float = 100000.0,
) -> DemographicMeasureResult:
    """
    Calculate Net Reproduction Rate (NRR) with Life Table Survival Integration (Fix B5).
    If life_table_female is not provided but mortality_schedule exists, constructs life table dynamically!
    Only falls back to approximate survival if zero mortality data exists.
    """
    method = "empirical_life_table_survival"
    status = "computed"
    assumptions = []
    
    # 1. Check if life table provided directly or can be built from mortality_schedule
    lt = life_table_female
    if lt is None and mortality_schedule is not None and not mortality_schedule.empty:
        try:
            lt, _ = build_abridged_life_table(mortality_schedule, radix=radix, sex="female")
        except Exception:
            lt = None

    if (fertility_schedule is not None) and (lt is not None) and ("nLx" in lt.columns):
        # Precise cohort-survival derivation: NRR = sum( ASFR_f_i * (nLx_i / l0) )
        fert_df = fertility_schedule.copy()
        merged = pd.merge(fert_df, lt, on="age_group", how="inner")
        if not merged.empty:
            f_birth_col = "female_births" if "female_births" in merged.columns else None
            if f_birth_col:
                asfr_f = merged[f_birth_col] / merged["female_pop"]
            else:
                asfr_f = (merged["births"] * female_birth_proportion) / merged["female_pop"]
                assumptions.append("Disaggregated female births not provided; derived via sex ratio at birth ~105.")
                
            nrr_val = float((asfr_f * (merged["nLx"] / radix)).sum())
            method = "life_table_survival_integration"
        else:
            base_grr = grr if grr is not None else (tfr * female_birth_proportion if tfr is not None else calculate_gross_reproduction_rate(fertility_schedule=fertility_schedule).raw_value)
            nrr_val = base_grr * female_survival_to_childbearing
            method = "approximate_survival_fallback"
            status = "approximate"
            assumptions.append(f"Life table age groups did not align with fertility groups; applied approximate survival p={female_survival_to_childbearing:.3f}.")
    else:
        if grr is None:
            if tfr is not None:
                grr = tfr * female_birth_proportion
            elif fertility_schedule is not None:
                grr = calculate_gross_reproduction_rate(fertility_schedule=fertility_schedule).raw_value
            else:
                raise ValueError("Must provide either GRR, TFR, or fertility schedule.")
        nrr_val = grr * female_survival_to_childbearing
        method = "approximate_survival_constant"
        status = "approximate"
        assumptions.append(f"Female life table not available; assumed average survival to childbearing of {female_survival_to_childbearing*100:.1f}%.")
        
    inputs = {
        "grr": grr,
        "method": method,
        "nrr": nrr_val,
        "life_table_used": (lt is not None),
    }
    plain_interp = generate_measure_interpretation("NRR", nrr_val, inputs)
    
    return DemographicMeasureResult(
        code="NRR",
        shortform="NRR",
        full_name="Net Reproduction Rate",
        name=format_measure_name("NRR", "Net Reproduction Rate (NRR)"),
        block="C: Fertility & Reproduction",
        raw_value=nrr_val,
        formatted_value=f"{nrr_val:.3f} surviving daughters per woman" + (" (Approximate)" if status=="approximate" else ""),
        unit="surviving daughters per woman",
        formula="NRR = sum( ASFR_f,i * (nLx / l0) )",
        citation="Preston et al. (2001), Ch. 5; Bhende & Kanitkar (2010), Ch. 8",
        plain_interpretation=plain_interp,
        status=status,
        method=method,
        assumptions=assumptions,
        inputs_used=inputs,
        notes=(
            "Computed using female life table person-years (nLx / l0). Exact generational replacement level is NRR = 1.000. If NRR > 1, population expands; if NRR < 1, population contracts long-term."
            if method == "life_table_survival_integration"
            else "Approximate survival multiplier used. Exact generational replacement level is NRR = 1.000. If NRR > 1, population expands; if NRR < 1, population contracts long-term."
        ),
    )


def compute_bongaarts_determinants(
    tfr: float,
    cm: float = 0.70,  # Marriage index: proportion of reproductive years lived in union
    cc: float = 0.85,  # Contraception index: 1 - 1.08 * u * e
    ca: float = 1.00,  # Induced abortion index
    ci: float = 0.75,  # Infecundability index (postpartum amenorrhea)
    total_fecundity: float = 15.3,
) -> Dict[str, Any]:
    """
    Bongaarts Proximate Determinants of Fertility Framework.
    Explains the quantitative link between biological fecundity (~15.3 births) and observed TFR.
    TFR = Cm * Cc * Ca * Ci * TF
    """
    model_tfr = cm * cc * ca * ci * total_fecundity
    return {
        "observed_tfr": tfr,
        "total_fecundity_ceiling": total_fecundity,
        "cm_marriage_index": cm,
        "cc_contraception_index": cc,
        "ca_abortion_index": ca,
        "ci_infecundability_index": ci,
        "modeled_tfr": model_tfr,
        "fertility_inhibiting_pct": (1.0 - (tfr / total_fecundity)) * 100.0,
    }


def _compute_block_c_core(dataset: DemographicDataset) -> Dict[str, DemographicMeasureResult]:
    """Compute all Block C fertility measures from a demographic dataset."""
    results: Dict[str, DemographicMeasureResult] = {}
    
    b_tot = dataset.total_live_births
    t_pop = dataset.total_population
    
    # 1. CBR
    if b_tot is not None and t_pop is not None:
        results["CBR"] = calculate_crude_birth_rate(b_tot, t_pop)
        
    # 2. GMFR / MBR (Fix B6: Never silently substitute total births if marital_births is missing)
    if dataset.marital_births is not None and dataset.married_women_15_49 is not None:
        results["MBR"] = calculate_marital_birth_rate(dataset.marital_births, dataset.married_women_15_49)
        
    # 3. GFR
    w_15_49 = dataset.total_women_15_49
    if w_15_49 is None and dataset.fertility_schedule is not None and "female_pop" in dataset.fertility_schedule.columns:
        w_15_49 = float(dataset.fertility_schedule["female_pop"].sum())
        
    if b_tot is not None and w_15_49 is not None and w_15_49 > 0:
        results["GFR"] = calculate_general_fertility_rate(b_tot, w_15_49)
        
    # 4. ASFR, TFR, MAC
    tfr_val = None
    if dataset.fertility_schedule is not None and not dataset.fertility_schedule.empty:
        asfr_res, asfr_df = calculate_age_specific_fertility_rates(dataset.fertility_schedule)
        results["ASFR"] = asfr_res
        
        tfr_res = calculate_total_fertility_rate(asfr_df)
        results["TFR"] = tfr_res
        tfr_val = tfr_res.raw_value
        
        results["MAC"] = calculate_mean_age_at_childbearing(asfr_df)
        
    # 5. GRR
    grr_val = None
    if tfr_val is not None:
        grr_res = calculate_gross_reproduction_rate(tfr=tfr_val, fertility_schedule=dataset.fertility_schedule)
        results["GRR"] = grr_res
        grr_val = grr_res.raw_value
        
    # 6. NRR (Fix B5: dynamically builds female life table if mortality schedule is available)
    if grr_val is not None:
        nrr_res = calculate_net_reproduction_rate(
            grr=grr_val,
            tfr=tfr_val,
            fertility_schedule=dataset.fertility_schedule,
            life_table_female=dataset.life_table_female,
            mortality_schedule=dataset.mortality_schedule,
        )
        results["NRR"] = nrr_res
        
    return results


def compute_block_c(dataset: DemographicDataset) -> Dict[str, DemographicMeasureResult]:
    """Core measures plus the additional measures from the class revision sheet."""
    from engine import extra_measures as _xm
    results = _compute_block_c_core(dataset)
    for k, v in _xm.compute_fertility_extras(dataset, results).items():
        results.setdefault(k, v)
    return results
