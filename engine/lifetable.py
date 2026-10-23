"""
Section 5: Life Tables (Complete & Abridged)
Constructs single-year and abridged demographic life tables from age-specific mortality rates.

Columns:
- x: Exact starting age
- n: Width of age interval
- nax: Average person-years lived by those dying in interval (separation factor)
- nMx: Age-specific central death rate (deaths / population)
- nqx: Probability of dying between ages x and x+n
- npx: Probability of surviving between ages x and x+n (1 - nqx)
- lx: Survivors to exact age x (radix l0 = 100,000)
- ndx: Number of deaths between ages x and x+n
- nLx: Person-years lived in interval
- Tx: Total person-years lived above age x
- ex: Complete expectation of life at age x

References:
- Preston, S. H., Heuveline, P., & Guillot, M. (2001). Demography, Ch. 3.
- Chiang, C. L. (1984). The Life Table and Its Applications. Robert E. Krieger.
- Coale, A. J., & Demeny, P. (1983). Regional Model Life Tables and Stable Populations.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np
import pandas as pd
from engine.base import DemographicMeasureResult
from engine.registry import format_measure_name, generate_measure_interpretation


def estimate_infant_separation_factor(m0: float, sex: str = "both") -> float:
    """
    Estimates 1a0 using Coale-Demeny / Preston et al. (2001) empirical formulas.
    For low mortality (m0 < 0.107): a0 = 0.05 + 3.0 * m0
    For high mortality: a0 = 0.35
    """
    if sex.lower() == "male":
        if m0 < 0.107:
            return 0.045 + 2.684 * m0
        return 0.330
    elif sex.lower() == "female":
        if m0 < 0.107:
            return 0.053 + 2.800 * m0
        return 0.350
    else:
        if m0 < 0.107:
            return 0.050 + 2.750 * m0
        return 0.340


def build_abridged_life_table(
    mortality_df: pd.DataFrame,
    radix: float = 100000.0,
    sex: str = "both",
) -> Tuple[pd.DataFrame, Dict[str, DemographicMeasureResult]]:
    """
    Builds an abridged life table from a DataFrame with ['age_group', 'population', 'deaths']
    or ['age_group', 'asdr'].
    """
    df = mortality_df.copy()
    if "asdr" not in df.columns:
        if "deaths" in df.columns and "population" in df.columns:
            df["asdr"] = (df["deaths"] / df["population"]) * 1000.0
        else:
            raise ValueError("mortality_df must contain 'asdr' or ('deaths' and 'population').")
            
    # Standardize age interval lengths and exact ages
    exact_ages = []
    intervals = []
    
    for lbl in df["age_group"]:
        s = str(lbl).strip()
        if "+" in s or "over" in s.lower():
            exact = int("".join(filter(str.isdigit, s)))
            exact_ages.append(exact)
            intervals.append(np.nan)  # open interval
        elif "-" in s:
            parts = s.split("-")
            low = int(parts[0])
            high = int(parts[1])
            exact_ages.append(low)
            intervals.append(high - low + 1)
        else:
            try:
                exact = int(s)
                exact_ages.append(exact)
                intervals.append(1)
            except ValueError:
                exact_ages.append(len(exact_ages) * 5)
                intervals.append(5)
                
    df["x"] = exact_ages
    df["n"] = intervals
    df = df.sort_values("x").reset_index(drop=True)
    
    # nMx (central death rate per person)
    df["nMx"] = df["asdr"] / 1000.0
    
    # Separation factor nax
    nax_vals = []
    for i, r in df.iterrows():
        n = r["n"]
        x = r["x"]
        mx = r["nMx"]
        if np.isnan(n):
            # open interval
            nax_vals.append(1.0 / mx if mx > 0 else 10.0)
        elif x == 0 and n == 1:
            nax_vals.append(estimate_infant_separation_factor(mx, sex))
        elif x == 0 and n == 5:
            # 0-4 group directly
            a0 = estimate_infant_separation_factor(mx, sex)
            nax_vals.append(a0 + 1.5)
        elif x == 1 and n == 4:
            # 1-4 group
            nax_vals.append(1.5)
        else:
            nax_vals.append(n / 2.0)
    df["nax"] = nax_vals
    
    # nqx (probability of dying)
    nqx_vals = []
    for i, r in df.iterrows():
        n = r["n"]
        mx = r["nMx"]
        ax = r["nax"]
        if np.isnan(n):
            nqx_vals.append(1.0)
        else:
            denom = 1.0 + (n - ax) * mx
            q = (n * mx) / denom if denom > 0 else 1.0
            nqx_vals.append(min(1.0, max(0.0, q)))
    df["nqx"] = nqx_vals
    df["npx"] = 1.0 - df["nqx"]
    
    # lx and ndx
    lx = [radix]
    ndx = []
    for i in range(len(df)):
        q = df.loc[i, "nqx"]
        d = lx[i] * q
        ndx.append(d)
        if i < len(df) - 1:
            lx.append(max(0.0, lx[i] - d))
    df["lx"] = lx
    df["ndx"] = ndx
    
    # nLx (person-years lived)
    nLx_vals = []
    for i, r in df.iterrows():
        n = r["n"]
        l_cur = r["lx"]
        d_cur = r["ndx"]
        ax = r["nax"]
        mx = r["nMx"]
        if np.isnan(n):
            # open interval: L = l / M
            L = l_cur / mx if mx > 0 else 0.0
        else:
            l_next = l_cur - d_cur
            L = n * l_next + ax * d_cur
        nLx_vals.append(L)
    df["nLx"] = nLx_vals
    
    # Tx (cumulative person years above x)
    df["Tx"] = df["nLx"][::-1].cumsum()[::-1]
    
    # ex (life expectancy)
    df["ex"] = df["Tx"] / df["lx"]
    
    # Derive core life table summary indicators
    results: Dict[str, DemographicMeasureResult] = {}
    
    # e0: Life expectancy at birth
    e0_val = float(df.loc[0, "ex"])
    inputs_e0 = {"e0": e0_val, "radix": radix}
    results["E0"] = DemographicMeasureResult(
        code="E0",
        shortform="e0",
        full_name="Life Expectancy at Birth",
        name=format_measure_name("E0", "Life Expectancy at Birth (e0)"),
        block="E: Life Tables",
        raw_value=e0_val,
        formatted_value=f"{e0_val:.2f} years",
        unit="years",
        formula="e0 = T0 / l0",
        citation="Preston et al. (2001), Ch. 3; Chiang (1984)",
        plain_interpretation=generate_measure_interpretation("E0", e0_val, inputs_e0),
        inputs_used=inputs_e0,
        notes="Average lifespan an individual would experience under constant period mortality rates."
    )
    
    # e65: Life expectancy at age 65
    row_65 = df[df["x"] == 65]
    if not row_65.empty:
        e65_val = float(row_65.iloc[0]["ex"])
        inputs_e65 = {"e65": e65_val, "total_lifespan": 65.0 + e65_val}
        results["E65"] = DemographicMeasureResult(
            code="E65",
            shortform="e65",
            full_name="Life Expectancy at Age 65",
            name=format_measure_name("E65", "Life Expectancy at Age 65 (e65)"),
            block="E: Life Tables",
            raw_value=e65_val,
            formatted_value=f"{e65_val:.2f} years (expected age at death: {65.0 + e65_val:.1f})",
            unit="years remaining",
            formula="e65 = T65 / l65",
            citation="Preston et al. (2001), Ch. 3",
            plain_interpretation=generate_measure_interpretation("E65", e65_val, inputs_e65),
            inputs_used=inputs_e65,
        )
        
    # 45q15: Adult mortality probability (15 to 60)
    row_15 = df[df["x"] == 15]
    row_60 = df[df["x"] == 60]
    if not row_15.empty and not row_60.empty:
        l15 = float(row_15.iloc[0]["lx"])
        l60 = float(row_60.iloc[0]["lx"])
        if l15 > 0:
            q45_val = (l15 - l60) / l15
            inputs_45q15 = {"45q15": q45_val, "l15": l15, "l60": l60}
            results["45Q15"] = DemographicMeasureResult(
                code="45Q15",
                shortform="45q15",
                full_name="Adult Mortality Probability",
                name=format_measure_name("45Q15", "Adult Mortality Probability (45q15)"),
                block="E: Life Tables",
                raw_value=q45_val,
                formatted_value=f"{q45_val * 100.0:.2f}% (or {q45_val * 1000.0:.1f} per 1,000)",
                unit="probability of dying (15-60)",
                formula="45q15 = 1 - (l60 / l15)",
                citation="UN Population Division; WHO Global Health Estimates",
                plain_interpretation=generate_measure_interpretation("45Q15", q45_val, inputs_45q15),
                inputs_used=inputs_45q15,
                notes="Standard international indicator of adult premature mortality."
            )
            
    return df, results


def build_complete_life_table(
    single_year_mortality_df: pd.DataFrame,
    radix: float = 100000.0,
    sex: str = "both",
) -> pd.DataFrame:
    """
    Constructs a complete (single-year) demographic life table (n=1 for every age).
    Expects DataFrame with columns: ['age', 'deaths', 'population'] or ['age', 'asdr'].
    """
    df = single_year_mortality_df.copy()
    age_col = "age" if "age" in df.columns else df.columns[0]
    df["x"] = df[age_col].astype(int)
    df["n"] = 1
    df = df.sort_values("x").reset_index(drop=True)
    
    if "asdr" in df.columns:
        df["1Mx"] = df["asdr"] / 1000.0
    else:
        df["1Mx"] = df["deaths"] / df["population"]
        
    m = len(df)
    # 1a0 separation factor
    m0 = float(df.loc[0, "1Mx"])
    a0 = estimate_infant_separation_factor(m0, sex=sex)
    
    ax_vals = [a0] + [0.5] * (m - 2) + [1.0 / max(1e-5, float(df.iloc[-1]["1Mx"]))]
    df["1ax"] = ax_vals
    
    # 1qx = 1Mx / (1 + (1 - 1ax) * 1Mx)
    qx_vals = []
    for i in range(m - 1):
        mx = float(df.loc[i, "1Mx"])
        ax = float(df.loc[i, "1ax"])
        denom = 1.0 + (1.0 - ax) * mx
        qx = (mx / denom) if denom > 0 else 1.0
        qx_vals.append(min(1.0, max(0.0, qx)))
    qx_vals.append(1.0)  # Open interval q = 1.0
    df["1qx"] = qx_vals
    df["1px"] = 1.0 - df["1qx"]
    
    # lx and 1dx
    lx = [radix]
    dx = []
    for i in range(m - 1):
        d = lx[-1] * df.loc[i, "1qx"]
        dx.append(d)
        lx.append(max(0.0, lx[-1] - d))
    dx.append(lx[-1])  # All remaining die in last interval
    df["lx"] = lx
    df["1dx"] = dx
    
    # 1Lx
    lx_arr = np.array(lx)
    dx_arr = np.array(dx)
    ax_arr = np.array(ax_vals)
    Lx = []
    for i in range(m - 1):
        Lx.append(lx_arr[i + 1] + ax_arr[i] * dx_arr[i])
    # Open interval Lx = lx / Mx
    last_mx = max(1e-5, float(df.iloc[-1]["1Mx"]))
    Lx.append(lx_arr[-1] / last_mx)
    df["1Lx"] = Lx
    
    # Tx and ex
    Tx = np.cumsum(Lx[::-1])[::-1]
    df["Tx"] = Tx
    df["ex"] = [Tx[i] / lx_arr[i] if lx_arr[i] > 0 else 0.0 for i in range(m)]
    
    return df


def build_multiple_decrement_table(
    abridged_mortality_df: pd.DataFrame,
    cause_columns: List[str],
    radix: float = 100000.0,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Constructs a multiple-decrement cause-deleted life table (Preston et al. 2001, Ch. 4).
    Calculates life expectancy gains (delta e0) when each specified cause of death is eliminated.
    """
    base_lt, base_ind = build_abridged_life_table(abridged_mortality_df, radix=radix)
    base_e0 = base_ind["E0"].raw_value
    
    gains: Dict[str, float] = {}
    df = abridged_mortality_df.copy()
    
    for cause in cause_columns:
        if cause in df.columns:
            # Eliminate cause: deaths_deleted = total_deaths - cause_deaths
            tot_deaths = df["deaths"] if "deaths" in df.columns else (df["asdr"] * df["population"] / 1000.0)
            cause_deaths = df[cause]
            del_deaths = np.maximum(0.0, tot_deaths - cause_deaths)
            
            df_del = df.copy()
            df_del["deaths"] = del_deaths
            if "population" in df_del.columns:
                df_del["asdr"] = (del_deaths / df_del["population"]) * 1000.0
                
            try:
                lt_del, ind_del = build_abridged_life_table(df_del, radix=radix)
                del_e0 = ind_del["E0"].raw_value
                gains[f"gain_if_eliminated_{cause}"] = round(max(0.0, del_e0 - base_e0), 2)
            except Exception:
                gains[f"gain_if_eliminated_{cause}"] = 0.0
                
    return base_lt, gains


def calculate_working_life_expectancy(
    life_table_df: pd.DataFrame,
    activity_rates_by_age: Dict[int, float],
) -> pd.DataFrame:
    """
    Constructs a Working Life Table from life table person-years nLx and labor force participation rates.
    Working life expectancy at age x: e^w_x = sum_{y >= x} (nLy * w_y) / lx
    """
    df = life_table_df.copy()
    if "nLx" not in df.columns or "lx" not in df.columns:
        raise ValueError("Life table must contain 'nLx' and 'lx' columns.")
        
    x_col = "x" if "x" in df.columns else df.columns[0]
    w_rates = []
    for x_val in df[x_col]:
        # Exact age match or nearest lower age in activity dictionary
        closest = 0.0
        for a, r in sorted(activity_rates_by_age.items()):
            if x_val >= a:
                closest = r
        w_rates.append(closest)
        
    df["activity_rate"] = w_rates
    df["working_nLx"] = df["nLx"] * df["activity_rate"]
    
    # Cumulative working person-years Tw_x
    tw_x = np.cumsum(df["working_nLx"].values[::-1])[::-1]
    df["Tw_x"] = tw_x
    df["working_ex"] = [tw_x[i] / df.loc[i, "lx"] if df.loc[i, "lx"] > 0 else 0.0 for i in range(len(df))]
    
    return df

