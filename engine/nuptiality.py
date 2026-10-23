"""
Section 6: Nuptiality & Marital Dynamics
Implements:
1. Singulate Mean Age at Marriage (SMAM) (Hajnal 1953) for males and females
2. Spousal Age Gap (SAG)
3. Definitive Celibacy Rate (CR at age 50)
4. Crude Marriage Rate (CMRg) & General Marriage Rate (GMRg)
5. Crude Divorce Rate (CDvR) & General Divorce Rate (GDvR)
6. Divorce-to-Marriage Ratio (DMR)
7. Marital status distribution (never married, married, widowed, divorced, separated)

References:
- Hajnal, J. (1953). Age at marriage and proportions marrying. Population Studies, 7(2):111-136.
- United Nations (1983). Manual X: Indirect Techniques for Demographic Estimation, Ch. 1.
- Shryock, H. S., & Siegel, J. S. (1976). The Methods and Materials of Demography, Ch. 19.
- Bhende, A., & Kanitkar, T. (2010). Principles of Population Studies, Ch. 9.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np
import pandas as pd

from engine.base import DemographicMeasureResult, DemographicDataset
from engine.registry import format_measure_name, generate_measure_interpretation


def calculate_smam(
    marital_status_df: pd.DataFrame,
    sex: str = "female",
    age_col: str = "age_group",
    single_col: str = "never_married",
    total_col: Optional[str] = "total",
) -> DemographicMeasureResult:
    """
    Calculate Singulate Mean Age at Marriage (SMAM) (Hajnal 1953).
    SMAM = (15 + 5 * sum(S_i for i in 15-19..45-49) - 50 * S_50) / (1 - S_50)
    where S_i is the proportion single in each 5-year age group,
    and S_50 is estimated as (S_45_49 + S_50_54) / 2.
    """
    df = marital_status_df.copy()
    if "sex" in df.columns:
        df = df[df["sex"].str.lower() == sex.lower()]
        
    if df.empty:
        raise ValueError(f"No marital status data found for sex '{sex}'.")
        
    # Map age groups
    df["age_clean"] = df[age_col].astype(str).str.strip()
    
    # Check total column
    if total_col not in df.columns or df[total_col].isnull().all():
        # Sum all status columns
        status_cols = [c for c in ["never_married", "single", "married", "widowed", "divorced", "separated"] if c in df.columns]
        df["total"] = df[status_cols].sum(axis=1)
        total_col = "total"
        
    single_col_name = single_col if single_col in df.columns else ("single" if "single" in df.columns else df.columns[1])
    df["prop_single"] = df[single_col_name] / df[total_col]
    
    prop_dict = dict(zip(df["age_clean"], df["prop_single"]))
    
    # Relevant 5-year groups from 15-19 up to 45-49
    req_groups = ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49"]
    s_vals = []
    for g in req_groups:
        val = prop_dict.get(g)
        if val is None:
            # Try alternate formats like 15 to 19
            alt = g.replace("-", " to ")
            val = prop_dict.get(alt, 0.0)
        s_vals.append(val)
        
    s_45_49 = s_vals[-1]
    s_50_54 = prop_dict.get("50-54", prop_dict.get("50 to 54", s_45_49))
    s_50 = (s_45_49 + s_50_54) / 2.0
    
    # Hajnal person-years formula
    a = 15.0 + 5.0 * sum(s_vals)
    b = 50.0 * s_50
    ever_marrying = 1.0 - s_50
    
    if ever_marrying <= 0:
        smam_val = 50.0
    else:
        smam_val = (a - b) / ever_marrying
        
    code = "SMAM_MALE" if sex.lower() == "male" else "SMAM_FEMALE"
    name = format_measure_name(code, f"Singulate Mean Age at Marriage — {sex.title()} (SMAM)")
    
    inputs = {
        "sex": sex,
        "smam": smam_val,
        "s_50_celibacy": s_50 * 100.0,
        "proportions_single": dict(zip(req_groups, s_vals)),
    }
    plain_interp = generate_measure_interpretation(code, smam_val, inputs)
    
    return DemographicMeasureResult(
        code=code,
        shortform=f"SMAM({sex[0].upper()})",
        full_name=f"Singulate Mean Age at Marriage ({sex.title()})",
        name=name,
        block="F: Nuptiality & Marital Dynamics",
        raw_value=smam_val,
        formatted_value=f"{smam_val:.1f} years",
        unit="years",
        formula="SMAM = (15 + 5 * sum(S_15-49) - 50 * S_50) / (1 - S_50)",
        citation="Hajnal, J. (1953). Population Studies, 7(2):111-136",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes=f"Average age at first marriage among those who marry before age 50 ({s_50*100:.1f}% remain definitively single at 50)."
    )


def calculate_spousal_age_gap(smam_male: float, smam_female: float) -> DemographicMeasureResult:
    """Calculate Spousal Age Gap (SAG): SMAM(Male) - SMAM(Female)."""
    gap_val = smam_male - smam_female
    inputs = {"smam_male": smam_male, "smam_female": smam_female, "gap": gap_val}
    plain_interp = generate_measure_interpretation("SPOUSAL_GAP", gap_val, inputs)
    
    return DemographicMeasureResult(
        code="SPOUSAL_GAP",
        shortform="SAG",
        full_name="Spousal Age Gap",
        name=format_measure_name("SPOUSAL_GAP", "Spousal Age Gap (SAG)"),
        block="F: Nuptiality & Marital Dynamics",
        raw_value=gap_val,
        formatted_value=f"{gap_val:.1f} years",
        unit="years",
        formula="SAG = SMAM(Male) - SMAM(Female)",
        citation="UN Demographic Guidelines; Bhende & Kanitkar (2010)",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="Measures gender age disparity at union formation; larger gaps are characteristic of traditional demographic regimes."
    )


def calculate_crude_marriage_rate(marriages: float, total_population: float, per: int = 1000) -> DemographicMeasureResult:
    """Calculate Crude Marriage Rate (CMRg)."""
    if total_population <= 0:
        raise ValueError("Total population must be strictly positive.")
    cmrg_val = (marriages / total_population) * float(per)
    inputs = {"marriages": marriages, "total_population": total_population, "per": per}
    plain_interp = generate_measure_interpretation("CMRG", cmrg_val, inputs)
    
    return DemographicMeasureResult(
        code="CMRG",
        shortform="CMRg",
        full_name="Crude Marriage Rate",
        name=format_measure_name("CMRG", "Crude Marriage Rate (CMRg)"),
        block="F: Nuptiality & Marital Dynamics",
        raw_value=cmrg_val,
        formatted_value=f"{cmrg_val:.2f} marriages per {per:,} population",
        unit=f"marriages per {per:,}",
        formula=f"CMRg = (Marriages / Total Population) * {per}",
        citation="Shryock & Siegel (1976), Ch. 19",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
    )


def calculate_crude_divorce_rate(divorces: float, total_population: float, per: int = 1000) -> DemographicMeasureResult:
    """Calculate Crude Divorce Rate (CDvR)."""
    if total_population <= 0:
        raise ValueError("Total population must be strictly positive.")
    cdvr_val = (divorces / total_population) * float(per)
    inputs = {"divorces": divorces, "total_population": total_population, "per": per}
    plain_interp = generate_measure_interpretation("CDVR", cdvr_val, inputs)
    
    return DemographicMeasureResult(
        code="CDVR",
        shortform="CDvR",
        full_name="Crude Divorce Rate",
        name=format_measure_name("CDVR", "Crude Divorce Rate (CDvR)"),
        block="F: Nuptiality & Marital Dynamics",
        raw_value=cdvr_val,
        formatted_value=f"{cdvr_val:.2f} divorces per {per:,} population",
        unit=f"divorces per {per:,}",
        formula=f"CDvR = (Divorces / Total Population) * {per}",
        citation="Shryock & Siegel (1976), Ch. 19",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
    )


def calculate_general_divorce_rate(divorces: float, married_population: float, per: int = 1000) -> DemographicMeasureResult:
    """Calculate General Divorce Rate (GDvR)."""
    if married_population <= 0:
        raise ValueError("Married population must be strictly positive.")
    gdvr_val = (divorces / married_population) * float(per)
    inputs = {"divorces": divorces, "married_population": married_population, "per": per}
    plain_interp = generate_measure_interpretation("GDVR", gdvr_val, inputs)
    
    return DemographicMeasureResult(
        code="GDVR",
        shortform="GDvR",
        full_name="General Divorce Rate",
        name=format_measure_name("GDVR", "General Divorce Rate (GDvR)"),
        block="F: Nuptiality & Marital Dynamics",
        raw_value=gdvr_val,
        formatted_value=f"{gdvr_val:.2f} divorces per {per:,} married persons",
        unit=f"divorces per {per:,} married persons",
        formula=f"GDvR = (Divorces / Married Population) * {per}",
        citation="Newell (1988); Bhende & Kanitkar (2010)",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
    )


def _compute_nuptiality_section_core(dataset: DemographicDataset) -> Dict[str, DemographicMeasureResult]:
    """Computes all nuptiality measures from available dataset tables."""
    results: Dict[str, DemographicMeasureResult] = {}
    
    t_pop = dataset.total_population
    
    # 1. SMAM from marital status distribution
    if dataset.marital_status_df is not None and not dataset.marital_status_df.empty:
        try:
            smam_f = calculate_smam(dataset.marital_status_df, sex="female")
            results["SMAM_FEMALE"] = smam_f
        except Exception:
            pass
        try:
            smam_m = calculate_smam(dataset.marital_status_df, sex="male")
            results["SMAM_MALE"] = smam_m
        except Exception:
            pass
            
        if "SMAM_FEMALE" in results and "SMAM_MALE" in results:
            results["SPOUSAL_GAP"] = calculate_spousal_age_gap(results["SMAM_MALE"].raw_value, results["SMAM_FEMALE"].raw_value)
            
    # 2. Crude Marriage Rate
    if dataset.marriages_total is not None and t_pop is not None and t_pop > 0:
        results["CMRG"] = calculate_crude_marriage_rate(dataset.marriages_total, t_pop)
        
    # 3. Divorce Rates
    if dataset.divorces_total is not None and t_pop is not None and t_pop > 0:
        results["CDVR"] = calculate_crude_divorce_rate(dataset.divorces_total, t_pop)
        
    # General Divorce Rate needs a real count of married persons. It is only computed when the
    # marital-status table supplies one; it is never approximated from married women (no silent inventions).
    married_persons = None
    mdf = dataset.marital_status_df
    if mdf is not None and not mdf.empty and "married" in mdf.columns:
        married_persons = float(pd.to_numeric(mdf["married"], errors="coerce").fillna(0).sum())
    if dataset.divorces_total is not None and married_persons and married_persons > 0:
        results["GDVR"] = calculate_general_divorce_rate(dataset.divorces_total, married_persons)

    return results


def simulate_marriage_age_shift(
    base_smam: float,
    base_tfr: float,
    shift_years: float = 2.0,
) -> Dict[str, Any]:
    """
    Simulates the quantitative demographic impact of raising the mean age at first marriage (Section 5.6b).
    Based on Bongaarts (1978) proximate determinants framework:
    Reproductive lifespan exposure (ages 15-49 = 35 years) decreases proportionally with delayed marriage:
    Cm' = (35 - (new_smam - 15)) / 35 = (50 - new_smam) / 35
    TFR_projected = TFR_base * (Cm' / Cm_base)
    """
    if base_smam < 15.0 or base_smam >= 50.0:
        raise ValueError("Baseline SMAM must be between 15 and 50 years.")
        
    cm_base = max(0.1, (50.0 - base_smam) / 35.0)
    new_smam = base_smam + shift_years
    cm_new = max(0.1, (50.0 - new_smam) / 35.0)
    
    ratio = cm_new / cm_base
    projected_tfr = base_tfr * ratio
    tfr_reduction = base_tfr - projected_tfr
    pct_reduction = (tfr_reduction / base_tfr) * 100.0 if base_tfr > 0 else 0.0
    
    return {
        "baseline_smam": round(base_smam, 2),
        "shifted_smam": round(new_smam, 2),
        "shift_years": shift_years,
        "baseline_cm_index": round(cm_base, 3),
        "projected_cm_index": round(cm_new, 3),
        "baseline_tfr": round(base_tfr, 2),
        "projected_tfr": round(projected_tfr, 2),
        "absolute_tfr_reduction": round(tfr_reduction, 2),
        "percent_fertility_reduction": round(pct_reduction, 1),
        "interpretation": (
            f"Postponing first marriage by +{shift_years:.1f} years (from SMAM {base_smam:.1f} to {new_smam:.1f} years) "
            f"reduces reproductive marital exposure (Cm: {cm_base:.2f} -> {cm_new:.2f}), "
            f"inducing an estimated {pct_reduction:.1f}% decline in fertility (TFR {base_tfr:.2f} -> {projected_tfr:.2f})."
        ),
    }


def compute_nuptiality_section(dataset: DemographicDataset) -> Dict[str, DemographicMeasureResult]:
    """Core measures plus the additional measures from the class revision sheet."""
    from engine import extra_measures as _xm
    results = _compute_nuptiality_section_core(dataset)
    for k, v in _xm.compute_nuptiality_extras(dataset).items():
        results.setdefault(k, v)
    return results
