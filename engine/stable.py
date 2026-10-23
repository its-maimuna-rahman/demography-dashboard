"""
Section 9: Stable & Stationary Populations
Implements:
1. Numerical solver for Lotka's characteristic equation to find the intrinsic rate of natural increase (r)
2. Intrinsic Birth Rate (b) & Intrinsic Death Rate (d)
3. Stable Age Distribution c(a)
4. Mean Length of Generation (T)
5. Stationary Population Relationships (b = d = 1 / e0)

References:
- Lotka, A. J. (1939). Théorie analytique des associations biologiques. Hermann & Cie.
- Preston, S. H., Heuveline, P., & Guillot, M. (2001). Demography, Ch. 7.
- Coale, A. J. (1972). The Growth and Structure of Human Populations. Princeton University Press.
"""

from __future__ import annotations
import math
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np
import pandas as pd

from engine.base import DemographicMeasureResult, DemographicDataset
from engine.registry import format_measure_name, generate_measure_interpretation
from engine.lifetable import build_abridged_life_table


def solve_lotka_intrinsic_r(
    fertility_schedule: pd.DataFrame,
    life_table_df: pd.DataFrame,
    female_birth_proportion: float = 100.0 / 205.0,
    radix: float = 100000.0,
    tol: float = 1e-6,
    max_iter: int = 100,
) -> Dict[str, Any]:
    """
    Numerically solves Lotka's characteristic renewal equation:
    sum( exp(-r * a_i) * f_female_i * (nLx_i / l0) ) = 1.0
    using the bisection method.
    """
    # Merge fertility schedule and life table
    df = pd.merge(fertility_schedule, life_table_df, on="age_group", how="inner")
    if df.empty:
        raise ValueError("Could not align age groups between fertility schedule and life table.")
        
    # Calculate female ASFR per person
    if "female_births" in df.columns:
        df["fx_female"] = df["female_births"] / df["female_pop"]
    else:
        df["fx_female"] = (df["births"] * female_birth_proportion) / df["female_pop"]
        
    # Extract age midpoints
    midpoints = []
    for lbl in df["age_group"]:
        parts = str(lbl).split("-")
        low = float(parts[0])
        high = float(parts[1]) if len(parts) > 1 else low + 4.0
        midpoints.append((low + high + 1.0) / 2.0)
    df["mid_age"] = midpoints
    
    # Net maternity function: phi(a) = fx_female * (nLx / radix)
    df["phi"] = df["fx_female"] * (df["nLx"] / radix)
    nrr = float(df["phi"].sum())
    
    # Define characteristic equation: Psi(r) = sum( exp(-r * a) * phi(a) ) - 1.0
    def psi(r: float) -> float:
        return float(np.sum(np.exp(-r * df["mid_age"]) * df["phi"])) - 1.0
        
    # Initial bounds for r
    # Approximation: r ≈ ln(NRR) / 28.0
    r_approx = math.log(nrr) / 28.0 if nrr > 0 else -0.05
    r_low = r_approx - 0.05
    r_high = r_approx + 0.05
    
    # Ensure bracket
    f_low = psi(r_low)
    f_high = psi(r_high)
    attempts = 0
    while f_low * f_high > 0 and attempts < 10:
        r_low -= 0.04
        r_high += 0.04
        f_low = psi(r_low)
        f_high = psi(r_high)
        attempts += 1
        
    if f_low * f_high > 0:
        r_root = r_approx
    else:
        # Bisection
        for _ in range(max_iter):
            r_mid = (r_low + r_high) / 2.0
            f_mid = psi(r_mid)
            if abs(f_mid) < tol or (r_high - r_low) / 2.0 < tol:
                r_root = r_mid
                break
            if f_low * f_mid < 0:
                r_high = r_mid
                f_high = f_mid
            else:
                r_low = r_mid
                f_low = f_mid
        else:
            r_root = (r_low + r_high) / 2.0
            
    # Intrinsic birth rate: b = 1 / sum( exp(-r * a) * (nLx / radix) )
    # Evaluated across all life table age groups
    lt_midpoints = []
    for lbl in life_table_df["age_group"]:
        s = str(lbl).replace("+", "")
        parts = s.split("-")
        low = float(parts[0])
        high = float(parts[1]) if len(parts) > 1 else low + 4.0
        lt_midpoints.append((low + high + 1.0) / 2.0)
    lt_mids = np.array(lt_midpoints)
    
    denom_b = float(np.sum(np.exp(-r_root * lt_mids) * (life_table_df["nLx"] / radix)))
    b_val = (1.0 / denom_b) * 1000.0 if denom_b > 0 else 15.0
    d_val = b_val - (r_root * 1000.0)
    
    # Mean length of generation: T = ln(NRR) / r
    gen_len = (math.log(nrr) / r_root) if (nrr > 0 and abs(r_root) > 1e-5) else 28.5
    
    return {
        "nrr": nrr,
        "intrinsic_r": float(r_root),
        "intrinsic_r_pct": float(r_root * 100.0),
        "intrinsic_birth_rate_per_1000": float(b_val),
        "intrinsic_death_rate_per_1000": float(d_val),
        "mean_length_generation_years": float(gen_len),
        "mid_maternity_age": float(df["mid_age"].mean()),
        "r1": float((df["mid_age"] * df["phi"]).sum()),
        "r2": float((df["mid_age"] ** 2 * df["phi"]).sum()),
    }


def compute_stable_population_measures(
    fertility_schedule: pd.DataFrame,
    mortality_schedule: pd.DataFrame,
) -> Dict[str, DemographicMeasureResult]:
    """Computes full suite of stable and stationary population parameters."""
    lt_df, _ = build_abridged_life_table(mortality_schedule, sex="female")
    sol = solve_lotka_intrinsic_r(fertility_schedule, lt_df)
    
    results = {}
    
    # 1. Intrinsic Rate of Natural Increase (r)
    r_pct = sol["intrinsic_r_pct"]
    inputs_r = {"r_pct": r_pct, "r_raw": sol["intrinsic_r"]}
    plain_r = generate_measure_interpretation("LOTKA_R", r_pct, inputs_r)
    results["LOTKA_R"] = DemographicMeasureResult(
        code="LOTKA_R",
        shortform="r_int",
        full_name="Intrinsic Rate of Natural Increase",
        name=format_measure_name("LOTKA_R", "Intrinsic Rate of Natural Increase (r_int)"),
        block="H: Stable Population & Renewal",
        raw_value=r_pct,
        formatted_value=f"{r_pct:+.2f}% per year",
        unit="% per year",
        formula="Root r of Lotka characteristic equation: sum( exp(-r * a) * f_f * nL / l0 ) = 1",
        citation="Lotka, A. J. (1939); Preston et al. (2001), Ch. 7",
        plain_interpretation=plain_r,
        inputs_used=inputs_r,
        notes="The stable growth rate a population will inevitably converge to if current vital rates remain fixed."
    )
    
    # 2. Intrinsic Birth Rate (b)
    b_val = sol["intrinsic_birth_rate_per_1000"]
    inputs_b = {"b": b_val}
    plain_b = generate_measure_interpretation("INTRINSIC_B", b_val, inputs_b)
    results["INTRINSIC_B"] = DemographicMeasureResult(
        code="INTRINSIC_B",
        shortform="b_int",
        full_name="Intrinsic Birth Rate",
        name=format_measure_name("INTRINSIC_B", "Intrinsic Birth Rate (b_int)"),
        block="H: Stable Population & Renewal",
        raw_value=b_val,
        formatted_value=f"{b_val:.2f} births per 1,000",
        unit="births per 1,000",
        formula="b = 1 / sum( exp(-r * a) * nL / l0 )",
        citation="Preston et al. (2001), Ch. 7",
        plain_interpretation=plain_b,
        inputs_used=inputs_b,
    )
    
    # 3. Intrinsic Death Rate (d)
    d_val = sol["intrinsic_death_rate_per_1000"]
    inputs_d = {"d": d_val}
    plain_d = generate_measure_interpretation("INTRINSIC_D", d_val, inputs_d)
    results["INTRINSIC_D"] = DemographicMeasureResult(
        code="INTRINSIC_D",
        shortform="d_int",
        full_name="Intrinsic Death Rate",
        name=format_measure_name("INTRINSIC_D", "Intrinsic Death Rate (d_int)"),
        block="H: Stable Population & Renewal",
        raw_value=d_val,
        formatted_value=f"{d_val:.2f} deaths per 1,000",
        unit="deaths per 1,000",
        formula="d = b - r",
        citation="Preston et al. (2001), Ch. 7",
        plain_interpretation=plain_d,
        inputs_used=inputs_d,
    )
    
    # 4. Mean Length of Generation (T)
    t_val = sol["mean_length_generation_years"]
    inputs_t = {"T": t_val}
    plain_t = generate_measure_interpretation("GEN_LEN", t_val, inputs_t)
    results["GEN_LEN"] = DemographicMeasureResult(
        code="GEN_LEN",
        shortform="T",
        full_name="Mean Length of Generation",
        name=format_measure_name("GEN_LEN", "Mean Length of Generation (T)"),
        block="H: Stable Population & Renewal",
        raw_value=t_val,
        formatted_value=f"{t_val:.1f} years",
        unit="years",
        formula="T = ln(NRR) / r",
        citation="Lotka (1939); Preston et al. (2001)",
        plain_interpretation=plain_t,
        inputs_used=inputs_t,
        notes="Average time required for a cohort of newborn daughters to replace their mothers."
    )

    # Moments of the net maternity function and the quadratic approximation (class revision sheet)
    from engine import extra_measures as xm
    r0, r1, r2 = sol["nrr"], sol["r1"], sol["r2"]
    results["R1"] = xm.make_result("R1", r1, {"R0": r0})
    results["R2"] = xm.make_result("R2", r2, {"R0": r0})
    quad = xm.quadratic_stable_parameters(r0, r1, r2)
    if quad:
        results["ALPHA"] = xm.make_result("ALPHA", quad["alpha"], {"R0": r0, "R1": r1})
        results["BETA"] = xm.make_result("BETA", quad["beta"], {"R0": r0, "R1": r1, "R2": r2})
        results["MU"] = xm.make_result("MU", quad["mu"], {"R0": r0, "R1": r1})
        results["R_QUAD"] = xm.make_result("R_QUAD", quad["r"] * 100.0, {"alpha": quad["alpha"], "beta": quad["beta"], "R0": r0})
        results["T_QUAD"] = xm.make_result("T_QUAD", quad["T"], {"alpha": quad["alpha"], "beta": quad["beta"], "r": quad["r"]})

    return results


def calculate_leslie_dominant_eigenvalue(
    intrinsic_r: float,
    step_years: int = 5,
) -> Dict[str, float]:
    """
    Calculates dominant eigenvalue of the Leslie projection matrix: lambda = exp(r * step_years).
    Property: If lambda > 1, population expands; lambda = 1 stationary equilibrium; lambda < 1 contracting.
    """
    lam = float(math.exp(intrinsic_r * float(step_years)))
    return {
        "dominant_eigenvalue_lambda": round(lam, 5),
        "step_years": step_years,
        "annual_multiplier": round(math.exp(intrinsic_r), 5),
        "asymptotic_state": "Expanding" if lam > 1.0001 else ("Contracting" if lam < 0.9999 else "Stationary"),
    }


def calculate_keyfitz_population_momentum(
    crude_birth_rate: float,
    life_expectancy_e0: float,
    nrr: float,
    mean_generation_length: float = 28.5,
) -> Dict[str, Any]:
    """
    Keyfitz (1971) Population Momentum Factor.
    Evaluates the ratio of the ultimate stationary population size to the initial population size
    if fertility were to drop immediately to replacement level (NRR = 1.000).
    Formula: M = (b * e0) / sqrt(NRR)
    where b is the initial birth rate per person, e0 is life expectancy at birth, and NRR is net reproduction rate.
    """
    b_per_person = crude_birth_rate / 1000.0 if crude_birth_rate > 1.0 else crude_birth_rate
    sqrt_nrr = math.sqrt(max(0.1, nrr))
    momentum_m = (b_per_person * life_expectancy_e0) / sqrt_nrr
    
    pct_growth = (momentum_m - 1.0) * 100.0
    
    return {
        "momentum_multiplier": round(momentum_m, 3),
        "ultimate_growth_percent": round(pct_growth, 1),
        "initial_cbr": round(crude_birth_rate, 2),
        "initial_e0": round(life_expectancy_e0, 1),
        "initial_nrr": round(nrr, 3),
        "interpretation": (
            f"If fertility were to drop immediately to the replacement level (NRR = 1.000), "
            f"the population would still expand by an estimated {pct_growth:+.1f}% (Momentum M = {momentum_m:.3f}) "
            f"before stabilizing, due to young age structure momentum."
        ),
    }

