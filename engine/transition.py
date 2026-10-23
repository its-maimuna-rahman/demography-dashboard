"""
Section 10: Demographic Transition & Theories
Implements:
1. Demographic Transition Stage Classifier (Thompson & Notestein framework)
2. Malthusian Population vs Subsistence Progression Demo

References:
- Notestein, F. W. (1945). Population — The Long View. Food for the World.
- Thompson, W. S. (1929). Population. American Journal of Sociology, 34(6):959-975.
- Malthus, T. R. (1798). An Essay on the Principle of Population. J. Johnson.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np


def classify_demographic_transition_stage(
    cbr: float,
    cdr: float,
    tfr: Optional[float] = None,
    life_expectancy: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Classifies a population into Demographic Transition Stages (1 to 5).
    """
    nir = cbr - cdr  # rate of natural increase per 1,000
    nir_pct = nir / 10.0
    
    stage = 3
    stage_title = "Stage 3: Late Expanding"
    description = ""
    demographic_characteristics = []
    
    if cbr >= 35.0 and cdr >= 28.0:
        stage = 1
        stage_title = "Stage 1: High Stationary (Pre-Industrial)"
        description = "High birth rates balanced by high fluctuating death rates, resulting in very low long-term growth and high child mortality."
        demographic_characteristics = ["High CBR (> 35)", "High CDR (> 28)", "Near zero natural increase (< 0.5%)", "Youthful age structure with low life expectancy"]
    elif cbr >= 28.0 and cdr < 20.0:
        stage = 2
        stage_title = "Stage 2: Early Expanding (Industrializing / Developing)"
        description = "Death rates decline precipitously due to improved sanitation, clean water, and antibiotics, while birth rates remain elevated, causing rapid demographic expansion."
        demographic_characteristics = ["High birth rate (> 28)", "Rapidly declining death rate (< 20)", "High natural increase (> 1.5% per annum)", "Expansive youth pyramid"]
    elif 16.0 <= cbr < 28.0 and cdr <= 14.0:
        stage = 3
        stage_title = "Stage 3: Late Expanding (Demographic Transitioning)"
        description = "Birth rates fall significantly due to urbanization, female education, delayed marriage, and family planning; death rates stabilize at low levels."
        demographic_characteristics = ["Declining CBR (16 - 28)", "Low stable CDR (< 14)", "Slowing natural increase (0.5% - 1.5%)", "Opening of prime demographic dividend window"]
    elif cbr < 16.0 and cdr <= 11.0 and nir >= 0.0:
        stage = 4
        stage_title = "Stage 4: Low Stationary (Post-Transition Modern)"
        description = "Both birth and death rates are low, stabilizing population growth near replacement level with an aging population structure."
        demographic_characteristics = ["Low CBR (< 16)", "Low CDR (< 11)", "Low or plateaued natural increase (0.0% - 0.5%)", "TFR near replacement (~2.1)", "Pillar-shaped population pyramid"]
    else:
        stage = 5
        stage_title = "Stage 5: Declining / Contractive (Post-Modern)"
        description = "Death rates exceed birth rates due to prolonged lowest-low sub-replacement fertility and elderly population momentum, leading to natural demographic contraction."
        demographic_characteristics = ["Lowest-low CBR (< 10-12)", "CDR exceeding CBR due to population aging", "Negative natural increase (< 0%)", "Inverted urn-shaped pyramid with shrinking workforce"]

    return {
        "stage": stage,
        "stage_title": stage_title,
        "cbr": cbr,
        "cdr": cdr,
        "nir_per_1000": nir,
        "nir_annual_pct": nir_pct,
        "tfr": tfr,
        "life_expectancy": life_expectancy,
        "description": description,
        "characteristics": demographic_characteristics,
        "interpretation": f"The population is classified in **{stage_title}**. With a CBR of {cbr:.1f} and CDR of {cdr:.1f}, natural increase is {nir_pct:+.2f}% annually.",
    }


def simulate_malthusian_dynamics(
    initial_population: float,
    growth_rate_pct: float,
    initial_subsistence: float,
    subsistence_growth_per_year: float,
    horizon_years: int = 50,
) -> Tuple[pd.DataFrame, Optional[int]]:
    """
    Simulates Thomas Malthus' classic thesis:
    - Population grows geometrically (exponentially): P(t) = P0 * (1 + r)^t
    - Subsistence / Food resources grow arithmetically (linearly): S(t) = S0 + k * t
    """
    years = list(range(horizon_years + 1))
    r = growth_rate_pct / 100.0
    
    pop_series = [initial_population * ((1.0 + r) ** t) for t in years]
    sub_series = [initial_subsistence + subsistence_growth_per_year * t for t in years]
    
    crossing_year = None
    for t, (p, s) in enumerate(zip(pop_series, sub_series)):
        if p > s and crossing_year is None:
            crossing_year = t
            
    df = pd.DataFrame({
        "year_step": years,
        "population_geometric": pop_series,
        "subsistence_arithmetic": sub_series,
        "deficit": [max(0.0, p - s) for p, s in zip(pop_series, sub_series)],
    })
    return df, crossing_year
