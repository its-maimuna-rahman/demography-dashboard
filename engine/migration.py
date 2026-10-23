"""
Section 7: Migration & Spatial Redistribution
Implements:
1. In-Migration Rate (IMRg)
2. Out-Migration Rate (OMRg)
3. Net Migration Rate (NMRg)
4. Gross Migration Rate (Turnover) (GMRg)
5. Migration Efficiency / Effectiveness Ratio (MER)
6. Residual (Vital Statistics) Method: Balancing Equation
7. Index of Population Redistribution (IPR)
8. Origin-Destination Migration Matrix and Streams

References:
- United Nations (1970). Manual VI: Methods of Measuring Internal Migration.
- Shryock, H. S., & Siegel, J. S. (1976). The Methods and Materials of Demography, Ch. 21.
- Rowland, D. T. (2003). Demographic Methods and Concepts, Ch. 11.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np
import pandas as pd

from engine.base import DemographicMeasureResult, DemographicDataset
from engine.registry import format_measure_name, generate_measure_interpretation


def calculate_migration_rates(
    in_migrants: float,
    out_migrants: float,
    midyear_population: float,
    per: int = 1000,
) -> Dict[str, DemographicMeasureResult]:
    """Calculates In-, Out-, Net-, and Gross Migration Rates, and Migration Efficiency Ratio."""
    if midyear_population <= 0:
        raise ValueError("Midyear population must be strictly positive.")
        
    net_m = in_migrants - out_migrants
    gross_m = in_migrants + out_migrants
    
    imr_val = (in_migrants / midyear_population) * float(per)
    omr_val = (out_migrants / midyear_population) * float(per)
    nmr_val = (net_m / midyear_population) * float(per)
    gmr_val = (gross_m / midyear_population) * float(per)
    mer_val = (abs(net_m) / gross_m * 100.0) if gross_m > 0 else 0.0
    
    results = {}
    
    # Net Migration Rate
    inputs_nmr = {"in_migrants": in_migrants, "out_migrants": out_migrants, "net_migrants": net_m, "midyear_pop": midyear_population, "per": per}
    plain_nmr = generate_measure_interpretation("NMRG", nmr_val, inputs_nmr)
    results["NMRG"] = DemographicMeasureResult(
        code="NMRG",
        shortform="NMRg",
        full_name="Net Migration Rate",
        name=format_measure_name("NMRG", "Net Migration Rate (NMRg)"),
        block="G: Migration & Spatial Redistribution",
        raw_value=nmr_val,
        formatted_value=f"{nmr_val:+.2f} migrants per {per:,} population",
        unit=f"migrants per {per:,}",
        formula="NMRg = ((In-Migrants - Out-Migrants) / Mid-Year Pop) * 1000",
        citation="UN Manual VI: Methods of Measuring Internal Migration",
        plain_interpretation=plain_nmr,
        inputs_used=inputs_nmr,
        notes="Positive indicates a net demographic influx; negative indicates net out-migration."
    )
    
    # Migration Efficiency Ratio
    inputs_mer = {"net_migrants": net_m, "gross_turnover": gross_m, "mer": mer_val}
    plain_mer = generate_measure_interpretation("MER", mer_val, inputs_mer)
    results["MER"] = DemographicMeasureResult(
        code="MER",
        shortform="MER",
        full_name="Migration Efficiency Ratio",
        name=format_measure_name("MER", "Migration Efficiency Ratio (MER)"),
        block="G: Migration & Spatial Redistribution",
        raw_value=mer_val,
        formatted_value=f"{mer_val:.1f}%",
        unit="%",
        formula="MER = ( |In - Out| / (In + Out) ) * 100",
        citation="Shryock & Siegel (1976), Ch. 21",
        plain_interpretation=plain_mer,
        inputs_used=inputs_mer,
        notes="High efficiency indicates unidirectional population movement; low efficiency indicates heavy two-way exchange."
    )
    
    return results


def calculate_residual_net_migration(
    pop_start: float,
    pop_end: float,
    births: float,
    deaths: float,
    period_years: float = 1.0,
) -> Dict[str, Any]:
    """
    Residual (Vital Statistics) Method using Demographic Balancing Equation.
    Net Migration = (P_end - P_start) - (Births - Deaths)
    """
    natural_increase = births - deaths
    total_change = pop_end - pop_start
    net_migration = total_change - natural_increase
    
    mid_pop = (pop_start + pop_end) / 2.0
    annual_nmr = (net_migration / mid_pop / period_years) * 1000.0 if mid_pop > 0 and period_years > 0 else 0.0
    
    return {
        "pop_start": pop_start,
        "pop_end": pop_end,
        "total_population_change": total_change,
        "natural_increase": natural_increase,
        "net_migration_count": net_migration,
        "annual_net_migration_rate_per_1000": annual_nmr,
        "period_years": period_years,
        "interpretation": f"Between censuses, natural increase contributed {natural_increase:,.0f} persons, leaving an estimated net migration of {net_migration:+,.0f} persons ({annual_nmr:+.2f} per 1,000 annually).",
    }


def compute_redistribution_index(
    regional_pop_df: pd.DataFrame,
    col_t1: str = "pop_t1",
    col_t2: str = "pop_t2",
) -> float:
    """
    Index of Population Redistribution (IPR).
    IPR = 0.5 * sum( |%_i,t2 - %_i,t1| )
    Measures percentage of national population that shifted between regions.
    """
    tot_t1 = regional_pop_df[col_t1].sum()
    tot_t2 = regional_pop_df[col_t2].sum()
    pct_t1 = (regional_pop_df[col_t1] / tot_t1) * 100.0
    pct_t2 = (regional_pop_df[col_t2] / tot_t2) * 100.0
    return float(0.5 * np.sum(np.abs(pct_t2 - pct_t1)))


def _compute_migration_section_core(dataset: DemographicDataset) -> Dict[str, DemographicMeasureResult]:
    """Computes all available migration measures from dataset inputs."""
    results: Dict[str, DemographicMeasureResult] = {}
    
    t_pop = dataset.total_population
    in_m = dataset.in_migrants
    out_m = dataset.out_migrants
    
    if in_m is not None and out_m is not None and t_pop is not None and t_pop > 0:
        rates = calculate_migration_rates(in_m, out_m, t_pop)
        results.update(rates)
        
    return results


def calculate_survival_ratio_migration(
    pop_t1_series: List[float],
    pop_t2_series: List[float],
    survival_ratios: List[float],
    age_groups: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Cohort Survival Ratio Migration Method (Census / Life-Table Survival Ratio).
    Formula: Net Migration_x+n = P_x+n(t2) - S_x * P_x(t1)
    where S_x is the cohort survival ratio over the intercensal interval.
    """
    m = min(len(pop_t1_series) - 1, len(pop_t2_series) - 1, len(survival_ratios))
    records = []
    
    for i in range(m):
        p1 = pop_t1_series[i]
        s_ratio = survival_ratios[i]
        expected_survivors = p1 * s_ratio
        actual_p2 = pop_t2_series[i + 1]
        net_mig = actual_p2 - expected_survivors
        
        lbl = age_groups[i + 1] if age_groups and i + 1 < len(age_groups) else f"Cohort {i+1}"
        records.append({
            "age_group": lbl,
            "population_t1": p1,
            "survival_ratio_Sx": round(s_ratio, 4),
            "expected_survivors_t2": round(expected_survivors, 1),
            "enumerated_pop_t2": round(actual_p2, 1),
            "net_migrants": round(net_mig, 1),
            "migration_rate_per_1000": round((net_mig / ((p1 + actual_p2) / 2.0)) * 1000.0, 2) if (p1 + actual_p2) > 0 else 0.0,
        })
        
    return pd.DataFrame(records)


def calculate_origin_destination_matrix(
    od_df: pd.DataFrame,
    origin_col: str = "origin",
    dest_col: str = "destination",
    flow_col: str = "migrants",
) -> Dict[str, Any]:
    """
    Origin-Destination Migration Stream Matrix & Efficiency.
    Evaluates gross flows, dominant streams, counter-streams, and net balance between regions.
    """
    matrix = od_df.pivot(index=origin_col, columns=dest_col, values=flow_col).fillna(0.0)
    
    total_out = matrix.sum(axis=1)
    total_in = matrix.sum(axis=0)
    net_stream = total_in - total_out
    
    total_movements = float(matrix.values.sum())
    net_redistribution = float(net_stream[net_stream > 0].sum())
    efficiency = (net_redistribution / total_movements * 100.0) if total_movements > 0 else 0.0
    
    return {
        "od_matrix": matrix,
        "total_in_migration": total_in.to_dict(),
        "total_out_migration": total_out.to_dict(),
        "net_migration_by_region": net_stream.to_dict(),
        "gross_interregional_flows": total_movements,
        "net_spatial_redistribution": net_redistribution,
        "spatial_effectiveness_index": round(efficiency, 2),
    }


def compute_migration_section(dataset: DemographicDataset) -> Dict[str, DemographicMeasureResult]:
    """Core measures plus the additional measures from the class revision sheet."""
    from engine import extra_measures as _xm
    results = _compute_migration_section_core(dataset)
    if dataset.in_migrants is not None and dataset.out_migrants is not None and dataset.total_population:
        for k, v in _xm.compute_migration_extras(dataset.in_migrants, dataset.out_migrants, dataset.total_population).items():
            results.setdefault(k, v)
    return results
