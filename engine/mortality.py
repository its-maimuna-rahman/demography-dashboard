"""
Block D / Section 4: Mortality & Age Standardization Measures
Implements:
1. Crude Death Rate (CDR)
2. Corrected CDR (CCDR) (Separate dual adjustments for census coverage and death registration completeness)
3. Neonatal Mortality Rate (NMR) (< 28 days)
4. Early Neonatal Mortality Rate (ENMR) (< 7 days)
5. Post-Neonatal Mortality Rate (PNMR) (28 days to 1 year)
6. Infant Mortality Rate (IMR) (< 1 year)
7. Child Death Rate 1-4 (CDR 1-4)
8. Under-5 Mortality Rate (U5MR) (< 5 years)
9. Maternal Mortality Ratio (MMR)
10. Age-Specific Death Rate (ASDR) Schedule
11. Direct Standardized Death Rate (DSDR) (Standardized to WHO or custom population)
12. Standardized Mortality Ratio (SMR) & Indirect Standardized Death Rate (ISDR)
13. Kitagawa Rate Decomposition

References:
- Preston, S. H., Heuveline, P., & Guillot, M. (2001). Demography, Ch. 2.
- World Health Organization (WHO) Statistical Standards & Global Health Estimates.
- Shryock, H. S., & Siegel, J. S. (1976). The Methods and Materials of Demography, Ch. 14 & 15.
- Chandra Sekar, C., & Deming, W. E. (1949). On a Method of Estimating Birth and Death Rates.
- Kitagawa, E. M. (1955). Components of a difference between two rates. JASA, 50(272):1168-1194.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, Union, List
import numpy as np
import pandas as pd

from engine.base import (
    DemographicMeasureResult,
    DemographicDataset,
    WHO_STANDARD_POPULATION_5YR,
    WHO_STANDARD_ASDR_5YR,
)
from engine.registry import format_measure_name, generate_measure_interpretation


def calculate_crude_death_rate(
    total_deaths: float,
    total_population: float,
    per: int = 1000,
) -> DemographicMeasureResult:
    """Calculate Crude Death Rate (CDR)."""
    if total_population <= 0:
        raise ValueError("Total population must be strictly positive.")
    if total_deaths < 0:
        raise ValueError("Total deaths cannot be negative.")
        
    cdr_val = (total_deaths / total_population) * float(per)
    inputs = {
        "total_deaths": total_deaths,
        "total_population": total_population,
        "per": per,
    }
    plain_interp = generate_measure_interpretation("CDR", cdr_val, inputs)
    
    return DemographicMeasureResult(
        code="CDR",
        shortform="CDR",
        full_name="Crude Death Rate",
        name=format_measure_name("CDR", "Crude Death Rate (CDR)"),
        block="D: Mortality & Standardization",
        raw_value=cdr_val,
        formatted_value=f"{cdr_val:.2f} deaths per {per:,} population",
        unit=f"deaths per {per:,}",
        formula=f"CDR = (Total Deaths / Total Mid-Year Population) * {per}",
        citation="Preston et al. (2001), Demography, Ch. 2",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="Influenced by age structure: an older population may have a higher CDR despite lower age-specific risks."
    )


def calculate_corrected_cdr(
    crude_death_rate: Optional[float] = None,
    total_deaths: Optional[float] = None,
    total_population: Optional[float] = None,
    death_registration_completeness: Optional[float] = None,
    census_coverage_rate: Optional[float] = None,
    completeness_rate: Optional[float] = None,
    per: int = 1000,
) -> DemographicMeasureResult:
    """
    Calculate Corrected Crude Death Rate (CCDR) (Fix B2 & B3).
    Separately adjusts numerator (deaths) for registration completeness and
    denominator (population) for census under-enumeration:
    
    True Deaths = D_obs / C_death
    True Population = P_census / C_census
    Corrected CDR = (True Deaths / True Population) * 1000 = CDR_raw * (C_census / C_death)
    """
    if death_registration_completeness is None and completeness_rate is not None:
        death_registration_completeness = completeness_rate

    if death_registration_completeness is None and census_coverage_rate is None:
        raise ValueError("Must provide at least death_registration_completeness or census_coverage_rate.")

    if crude_death_rate is None:
        if total_deaths is None or total_population is None:
            raise ValueError("Must provide either crude_death_rate or both total_deaths and total_population.")
        crude_death_rate = (total_deaths / total_population) * float(per)
        
    c_death = death_registration_completeness if death_registration_completeness is not None else 1.0
    c_census = census_coverage_rate if census_coverage_rate is not None else 1.0
    
    if c_death <= 0 or c_death > 1.0:
        raise ValueError("Death registration completeness must be in the range (0.0, 1.0].")
    if c_census <= 0 or c_census > 1.0:
        raise ValueError("Census coverage rate must be in the range (0.0, 1.0].")
        
    # Corrected CDR: D_true / P_true
    corrected_cdr_val = crude_death_rate * (c_census / c_death)
    
    inputs = {
        "crude_death_rate": crude_death_rate,
        "death_registration_completeness": c_death,
        "census_coverage_rate": c_census,
        "per": per,
    }
    plain_interp = generate_measure_interpretation("CORRECTED_CDR", corrected_cdr_val, inputs)
    
    return DemographicMeasureResult(
        code="CORRECTED_CDR",
        shortform="CCDR",
        full_name="Corrected Crude Death Rate",
        name=format_measure_name("CORRECTED_CDR", "Corrected Crude Death Rate (CCDR)"),
        block="D: Mortality & Standardization",
        raw_value=corrected_cdr_val,
        formatted_value=f"{corrected_cdr_val:.2f} deaths per {per:,} (adj. at {c_death*100:.1f}% death comp., {c_census*100:.1f}% census cov.)",
        unit=f"adjusted deaths per {per:,}",
        formula="CCDR = (Deaths / C_death) / (Pop / C_census) * 1000",
        citation="UN Principles and Recommendations for Vital Statistics; Chandra Sekar & Deming (1949)",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes=f"Corrects for {(1.0 - c_death)*100:.1f}% death under-registration and {(1.0 - c_census)*100:.1f}% census omission."
    )


def calculate_neonatal_mortality_rate(
    neonatal_deaths: float,
    total_live_births: float,
    per: int = 1000,
) -> DemographicMeasureResult:
    """Calculate Neonatal Mortality Rate (NMR)."""
    if total_live_births <= 0:
        raise ValueError("Total live births must be strictly positive.")
    if neonatal_deaths < 0:
        raise ValueError("Neonatal deaths cannot be negative.")
        
    nmr_val = (neonatal_deaths / total_live_births) * float(per)
    inputs = {
        "neonatal_deaths": neonatal_deaths,
        "total_live_births": total_live_births,
        "per": per,
    }
    plain_interp = generate_measure_interpretation("NMR", nmr_val, inputs)
    
    return DemographicMeasureResult(
        code="NMR",
        shortform="NMR",
        full_name="Neonatal Mortality Rate",
        name=format_measure_name("NMR", "Neonatal Mortality Rate (NMR)"),
        block="D: Mortality & Standardization",
        raw_value=nmr_val,
        formatted_value=f"{nmr_val:.2f} deaths per {per:,} live births",
        unit=f"deaths per {per:,} live births",
        formula=f"NMR = (Deaths < 28 days / Live Births) * {per}",
        citation="WHO Global Health Observatory; SDG Target 3.2",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="Primary indicator of perinatal care, skilled birth attendance, and newborn clinical management."
    )


def calculate_early_neonatal_mortality_rate(
    early_neonatal_deaths: float,
    total_live_births: float,
    per: int = 1000,
) -> DemographicMeasureResult:
    """Calculate Early Neonatal Mortality Rate (ENMR) (< 7 days)."""
    if total_live_births <= 0:
        raise ValueError("Total live births must be strictly positive.")
    enmr_val = (early_neonatal_deaths / total_live_births) * float(per)
    inputs = {"early_neonatal_deaths": early_neonatal_deaths, "total_live_births": total_live_births, "per": per}
    plain_interp = generate_measure_interpretation("ENMR", enmr_val, inputs)
    
    return DemographicMeasureResult(
        code="ENMR",
        shortform="ENMR",
        full_name="Early Neonatal Mortality Rate",
        name=format_measure_name("ENMR", "Early Neonatal Mortality Rate (ENMR)"),
        block="D: Mortality & Standardization",
        raw_value=enmr_val,
        formatted_value=f"{enmr_val:.2f} deaths per {per:,} live births",
        unit=f"deaths per {per:,} live births",
        formula=f"ENMR = (Deaths < 7 days / Live Births) * {per}",
        citation="WHO Guidelines; Preston et al. (2001)",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
    )


def calculate_post_neonatal_mortality_rate(
    infant_deaths: float,
    neonatal_deaths: float,
    total_live_births: float,
    per: int = 1000,
) -> DemographicMeasureResult:
    """Calculate Post-Neonatal Mortality Rate (PNMR) (28 days to 1 year)."""
    if total_live_births <= 0:
        raise ValueError("Total live births must be strictly positive.")
    pnm_deaths = infant_deaths - neonatal_deaths
    pnmr_val = (pnm_deaths / total_live_births) * float(per)
    inputs = {"infant_deaths": infant_deaths, "neonatal_deaths": neonatal_deaths, "total_live_births": total_live_births, "per": per}
    plain_interp = generate_measure_interpretation("PNMR", pnmr_val, inputs)
    
    return DemographicMeasureResult(
        code="PNMR",
        shortform="PNMR",
        full_name="Post-Neonatal Mortality Rate",
        name=format_measure_name("PNMR", "Post-Neonatal Mortality Rate (PNMR)"),
        block="D: Mortality & Standardization",
        raw_value=pnmr_val,
        formatted_value=f"{pnmr_val:.2f} deaths per {per:,} live births",
        unit=f"deaths per {per:,} live births",
        formula=f"PNMR = ((Deaths < 1 yr - Deaths < 28 days) / Live Births) * {per}",
        citation="WHO Child Health Guidelines",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="Reflects environmental sanitary conditions, nutrition, and infectious disease prevention post-discharge."
    )


def calculate_infant_mortality_rate(
    infant_deaths: float,
    total_live_births: float,
    per: int = 1000,
) -> DemographicMeasureResult:
    """Calculate Infant Mortality Rate (IMR)."""
    if total_live_births <= 0:
        raise ValueError("Total live births must be strictly positive.")
    if infant_deaths < 0:
        raise ValueError("Infant deaths cannot be negative.")
        
    imr_val = (infant_deaths / total_live_births) * float(per)
    inputs = {
        "infant_deaths": infant_deaths,
        "total_live_births": total_live_births,
        "per": per,
    }
    plain_interp = generate_measure_interpretation("IMR", imr_val, inputs)
    
    return DemographicMeasureResult(
        code="IMR",
        shortform="IMR",
        full_name="Infant Mortality Rate",
        name=format_measure_name("IMR", "Infant Mortality Rate (IMR)"),
        block="D: Mortality & Standardization",
        raw_value=imr_val,
        formatted_value=f"{imr_val:.2f} deaths per {per:,} live births",
        unit=f"deaths per {per:,} live births",
        formula=f"IMR = (Deaths < 1 year / Live Births) * {per}",
        citation="UNICEF / WHO Child Mortality Guidelines; Preston et al. (2001), Ch. 2",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="Fundamental bellwether indicator of national public health, socioeconomic equity, and basic sanitation."
    )


def calculate_child_mortality_rate(
    child_deaths_1_4: Optional[float] = None,
    pop_1_4: Optional[float] = None,
    under_5_deaths: Optional[float] = None,
    total_live_births: Optional[float] = None,
    per: int = 1000,
) -> DemographicMeasureResult:
    """Calculate Child Death Rate (CDR 1-4) (Fix B10: separate from U5MR)."""
    if child_deaths_1_4 is not None and pop_1_4 is not None and pop_1_4 > 0:
        cmr_val = (child_deaths_1_4 / pop_1_4) * float(per)
        inputs = {"child_deaths_1_4": child_deaths_1_4, "pop_1_4": pop_1_4, "per": per}
        plain_interp = generate_measure_interpretation("CMR", cmr_val, inputs)
        return DemographicMeasureResult(
            code="CMR",
            shortform="CDR(1-4)",
            full_name="Child Death Rate (Age 1-4)",
            name=format_measure_name("CMR", "Child Death Rate (CDR 1-4)"),
            block="D: Mortality & Standardization",
            raw_value=cmr_val,
            formatted_value=f"{cmr_val:.2f} deaths per {per:,} children (1-4)",
            unit=f"deaths per {per:,} children (1-4)",
            formula=f"CDR(1-4) = (Deaths 1-4 / Population 1-4) * {per}",
            citation="Preston et al. (2001), Ch. 2; Shryock & Siegel (1976)",
            plain_interpretation=plain_interp,
            inputs_used=inputs,
            notes="Evaluates child health risk between the 1st and 5th birthdays (highly sensitive to nutrition and infectious disease)."
        )
    elif under_5_deaths is not None and total_live_births is not None and total_live_births > 0:
        return calculate_under_5_mortality_rate(under_5_deaths, total_live_births, per=per)
    else:
        raise ValueError("Must provide either (child_deaths_1_4 and pop_1_4) or (under_5_deaths and total_live_births).")


def calculate_under_5_mortality_rate(
    under_5_deaths: float,
    total_live_births: float,
    per: int = 1000,
) -> DemographicMeasureResult:
    """Calculate Under-5 Mortality Rate (U5MR)."""
    if total_live_births <= 0:
        raise ValueError("Total live births must be strictly positive.")
    u5mr_val = (under_5_deaths / total_live_births) * float(per)
    inputs = {"under_5_deaths": under_5_deaths, "total_live_births": total_live_births, "per": per}
    plain_interp = generate_measure_interpretation("U5MR", u5mr_val, inputs)
    
    return DemographicMeasureResult(
        code="U5MR",
        shortform="U5MR",
        full_name="Under-5 Mortality Rate",
        name=format_measure_name("U5MR", "Under-5 Mortality Rate (U5MR)"),
        block="D: Mortality & Standardization",
        raw_value=u5mr_val,
        formatted_value=f"{u5mr_val:.2f} deaths per {per:,} live births",
        unit=f"deaths per {per:,} live births",
        formula=f"U5MR = (Deaths < 5 years / Live Births) * {per}",
        citation="UN IGME Child Mortality Estimation; SDG Indicator 3.2.1",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="SDG Target 3.2.1 aims for an Under-5 Mortality Rate of <= 25 per 1,000 live births."
    )


def calculate_maternal_mortality_ratio(
    maternal_deaths: float,
    total_live_births: float,
    per: int = 100000,
) -> DemographicMeasureResult:
    """Calculate Maternal Mortality Ratio (MMR)."""
    if total_live_births <= 0:
        raise ValueError("Total live births must be strictly positive.")
    mmr_val = (maternal_deaths / total_live_births) * float(per)
    inputs = {"maternal_deaths": maternal_deaths, "total_live_births": total_live_births, "per": per}
    plain_interp = generate_measure_interpretation("MMR", mmr_val, inputs)
    
    return DemographicMeasureResult(
        code="MMR",
        shortform="MMR",
        full_name="Maternal Mortality Ratio",
        name=format_measure_name("MMR", "Maternal Mortality Ratio (MMR)"),
        block="D: Mortality & Standardization",
        raw_value=mmr_val,
        formatted_value=f"{mmr_val:.1f} maternal deaths per 100,000 live births",
        unit="maternal deaths per 100,000 live births",
        formula=f"MMR = (Maternal Deaths / Live Births) * {per:,}",
        citation="WHO / UNICEF / UNFPA Maternal Mortality Estimates; SDG Target 3.1",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
    )


def calculate_age_specific_death_rates(
    mortality_schedule: pd.DataFrame,
    per: int = 1000,
) -> Tuple[DemographicMeasureResult, pd.DataFrame]:
    """Calculate Age-Specific Death Rates (ASDR)."""
    df = mortality_schedule.copy()
    if "population" not in df.columns or "deaths" not in df.columns:
        raise ValueError("mortality_schedule must contain 'population' and 'deaths' columns.")
        
    df["asdr"] = (df["deaths"] / df["population"]) * float(per)
    asdr_dict = dict(zip(df["age_group"], df["asdr"]))
    
    min_row = df.loc[df["asdr"].idxmin()] if not df.empty else None
    min_age = min_row["age_group"] if min_row is not None else "N/A"
    min_val = min_row["asdr"] if min_row is not None else 0.0
    
    inputs = {
        "asdr_schedule": asdr_dict,
        "lowest_mortality_age_group": min_age,
        "lowest_mortality_rate": min_val,
        "mean_asdr": float(df["asdr"].mean()),
    }
    plain_interp = generate_measure_interpretation("ASDR", min_val, inputs)
    
    return DemographicMeasureResult(
        code="ASDR",
        shortform="ASDR",
        full_name="Age-Specific Death Rate",
        name=format_measure_name("ASDR", "Age-Specific Death Rate (ASDR)"),
        block="D: Mortality & Standardization",
        raw_value=min_val,
        formatted_value=f"U-shaped curve (Minimum risk: {min_val:.2f} per {per:,} at Age {min_age})",
        unit=f"deaths per {per:,} population in age group",
        formula=f"ASDR_i = (Deaths_i / Population_i) * {per}",
        citation="Preston et al. (2001), Ch. 2; Shryock & Siegel (1976)",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="Standard biological mortality profile: elevated in infancy, minimum in late childhood (10-14), followed by exponential increase."
    ), df


def calculate_direct_standardized_rate(
    mortality_schedule: pd.DataFrame,
    standard_population: Optional[pd.DataFrame] = None,
    per: int = 1000,
) -> DemographicMeasureResult:
    """Calculate Direct Standardized Death Rate (DSDR) (Fix B4: clean age group matching)."""
    df = mortality_schedule.copy()
    if "asdr" not in df.columns:
        if "deaths" in df.columns and "population" in df.columns:
            df["asdr"] = (df["deaths"] / df["population"]) * float(per)
        else:
            raise ValueError("mortality_schedule must contain 'asdr' or ('deaths' and 'population').")
            
    if standard_population is not None:
        std_df = standard_population.copy()
        std_col = "standard_pop" if "standard_pop" in std_df.columns else ("population_std" if "population_std" in std_df.columns else std_df.columns[-1])
        merged = pd.merge(df, std_df, on="age_group", how="inner")
        if merged.empty:
            raise ValueError("No matching age groups found between study mortality schedule and standard population.")
        expected_deaths = (merged["asdr"] * merged[std_col]).sum() / float(per)
        total_std_pop = merged[std_col].sum()
        dsdr_val = (expected_deaths / total_std_pop) * float(per)
        std_name = "User Provided Standard Population"
    else:
        # Match against WHO 2000-2025 standard
        who_df = pd.DataFrame(list(WHO_STANDARD_POPULATION_5YR.items()), columns=["age_group", "std_pop"])
        merged = pd.merge(df, who_df, on="age_group", how="inner")
        if merged.empty:
            # Try cleaning labels
            df["clean_group"] = df["age_group"].str.strip().str.replace(" to ", "-").str.replace(" and over", "+")
            merged = pd.merge(df, who_df, left_on="clean_group", right_on="age_group", how="inner")
            
        if merged.empty:
            raise ValueError("Age groups in mortality schedule do not match standard 5-year groupings (0-4, 5-9, ..., 85+).")
            
        expected_deaths = (merged["asdr"] * merged["std_pop"]).sum() / float(per)
        total_std_pop = merged["std_pop"].sum()
        dsdr_val = (expected_deaths / total_std_pop) * float(per)
        std_name = "WHO World Standard Population (2000-2025)"
        
    inputs = {
        "standard_population_type": std_name,
        "total_standard_population": float(total_std_pop),
        "expected_standard_deaths": float(expected_deaths),
        "matched_age_groups_count": len(merged),
    }
    plain_interp = generate_measure_interpretation("DSDR", dsdr_val, inputs)
    
    return DemographicMeasureResult(
        code="DSDR",
        shortform="DSDR",
        full_name="Direct Standardized Death Rate",
        name=format_measure_name("DSDR", "Direct Standardized Death Rate (DSDR)"),
        block="D: Mortality & Standardization",
        raw_value=dsdr_val,
        formatted_value=f"{dsdr_val:.2f} standardized deaths per {per:,} ({std_name})",
        unit=f"standardized deaths per {per:,}",
        formula="DSDR = sum( ASDR_i * P_std_i ) / sum( P_std_i )",
        citation="WHO Guidelines for Standardized Rates; Preston et al. (2001), Ch. 2",
        plain_interpretation=plain_interp,
        inputs_used=inputs,
        notes="Removes age-structure confounding, enabling direct geographic and longitudinal mortality comparisons."
    )


def calculate_smr_and_indirect_standardized_rate(
    observed_deaths: float,
    mortality_schedule: pd.DataFrame,
    standard_population: Optional[pd.DataFrame] = None,
    standard_rates: Optional[pd.DataFrame] = None,
    standard_crude_death_rate: Optional[float] = None,
    use_who_standard_reference: bool = True,
    per: int = 1000,
) -> Tuple[DemographicMeasureResult, DemographicMeasureResult]:
    """
    Calculate Standardized Mortality Ratio (SMR) and Indirect Standardized Death Rate (ISDR) (Fix B1).
    Strictly requires external standard rates (or WHO standard reference schedule).
    Never uses the study population's own rates to avoid tautological SMR = 1.000.
    """
    df = mortality_schedule.copy()
    if "population" not in df.columns:
        raise ValueError("mortality_schedule must contain 'population' column.")
        
    expected_deaths: Optional[float] = None
    std_name = "External Standard"
    
    # 1. Check standard_rates parameter
    if standard_rates is not None and "asdr_std" in standard_rates.columns:
        merged = pd.merge(df, standard_rates, on="age_group", how="inner")
        if not merged.empty:
            expected_deaths = (merged["population"] * merged["asdr_std"] / float(per)).sum()
            std_name = "User Standard Rates"
            
    # 2. Check standard_population parameter
    if expected_deaths is None and standard_population is not None:
        if "asdr_std" in standard_population.columns:
            merged = pd.merge(df, standard_population, on="age_group", how="inner")
            expected_deaths = (merged["population"] * merged["asdr_std"] / float(per)).sum()
        elif "deaths_std" in standard_population.columns and "population_std" in standard_population.columns:
            merged = pd.merge(df, standard_population, on="age_group", how="inner")
            asdr_std = (merged["deaths_std"] / merged["population_std"]) * float(per)
            expected_deaths = (merged["population"] * asdr_std / float(per)).sum()
            if standard_crude_death_rate is None:
                standard_crude_death_rate = (standard_population["deaths_std"].sum() / standard_population["population_std"].sum()) * float(per)
        std_name = "User Standard Population"
        
    # 3. Fallback to bundled WHO World Standard ASDR Reference
    if expected_deaths is None and use_who_standard_reference:
        who_asdr_df = pd.DataFrame(list(WHO_STANDARD_ASDR_5YR.items()), columns=["age_group", "asdr_std"])
        merged = pd.merge(df, who_asdr_df, on="age_group", how="inner")
        if not merged.empty:
            expected_deaths = (merged["population"] * merged["asdr_std"] / float(per)).sum()
            std_name = "WHO World Standard Schedule"
            if standard_crude_death_rate is None:
                standard_crude_death_rate = 8.5
                
    if expected_deaths is None or expected_deaths <= 0:
        raise ValueError("Standard age-specific death rates are required to compute SMR and ISDR.")
        
    smr_val = observed_deaths / expected_deaths
    if standard_crude_death_rate is None:
        standard_crude_death_rate = 8.0
        
    isdr_val = smr_val * standard_crude_death_rate
    
    inputs_smr = {
        "observed_deaths": observed_deaths,
        "expected_deaths": expected_deaths,
        "standard_schedule": std_name,
        "smr": smr_val,
    }
    inputs_isdr = {
        "smr": smr_val,
        "standard_cdr": standard_crude_death_rate,
        "per": per,
    }
    
    plain_interp_smr = generate_measure_interpretation("SMR", smr_val, inputs_smr)
    plain_interp_isdr = generate_measure_interpretation("ISDR", isdr_val, inputs_isdr)
    
    smr_res = DemographicMeasureResult(
        code="SMR",
        shortform="SMR",
        full_name="Standardized Mortality Ratio",
        name=format_measure_name("SMR", "Standardized Mortality Ratio (SMR)"),
        block="D: Mortality & Standardization",
        raw_value=smr_val,
        formatted_value=f"{smr_val:.3f} ({smr_val*100:.1f}%) [Obs: {observed_deaths:,.0f} / Exp: {expected_deaths:,.1f}]",
        unit="ratio (Obs / Exp)",
        formula="SMR = Observed Deaths / Expected Deaths = D / sum( P_i * ASDR_std_i )",
        citation="Breslow & Day (1987); Preston et al. (2001), Ch. 2",
        plain_interpretation=plain_interp_smr,
        inputs_used=inputs_smr,
        notes=f"Evaluated against {std_name}. SMR > 1.0 indicates excess mortality relative to standard age-specific risk."
    )
    
    isdr_res = DemographicMeasureResult(
        code="ISDR",
        shortform="ISDR",
        full_name="Indirect Standardized Death Rate",
        name=format_measure_name("ISDR", "Indirect Standardized Death Rate (ISDR)"),
        block="D: Mortality & Standardization",
        raw_value=isdr_val,
        formatted_value=f"{isdr_val:.2f} deaths per {per:,} ({std_name})",
        unit=f"indirectly standardized deaths per {per:,}",
        formula="ISDR = SMR * Standard CDR",
        citation="Shryock & Siegel (1976), Ch. 14; Preston et al. (2001)",
        plain_interpretation=plain_interp_isdr,
        inputs_used=inputs_isdr,
        notes="Ideal when age-specific death counts in small subpopulations are sparse or unstable."
    )
    
    return smr_res, isdr_res


def compute_kitagawa_decomposition(
    cdr_1: float,
    cdr_2: float,
    age_dist_1: np.ndarray,
    age_dist_2: np.ndarray,
    asdr_1: np.ndarray,
    asdr_2: np.ndarray,
) -> Dict[str, Any]:
    """
    Kitagawa Rate Decomposition.
    Decomposes the difference between two crude death rates into:
    1. Age composition effect (due to differences in population age structure)
    2. Mortality schedule effect (due to differences in age-specific mortality rates)
    
    Delta = CDR_1 - CDR_2 = Rate Effect + Composition Effect
    """
    rate_effect = np.sum((asdr_1 - asdr_2) * (age_dist_1 + age_dist_2) / 2.0)
    composition_effect = np.sum((age_dist_1 - age_dist_2) * (asdr_1 + asdr_2) / 2.0)
    total_diff = cdr_1 - cdr_2
    
    return {
        "cdr_population_1": cdr_1,
        "cdr_population_2": cdr_2,
        "total_difference": total_diff,
        "rate_effect": float(rate_effect),
        "composition_effect": float(composition_effect),
        "rate_effect_pct": float(rate_effect / total_diff * 100.0) if total_diff != 0 else 0.0,
        "composition_effect_pct": float(composition_effect / total_diff * 100.0) if total_diff != 0 else 0.0,
    }


def compute_block_d(dataset: DemographicDataset) -> Dict[str, DemographicMeasureResult]:
    """Compute all Block D mortality & standardization measures from a demographic dataset."""
    results: Dict[str, DemographicMeasureResult] = {}
    
    d_tot = dataset.total_deaths
    t_pop = dataset.total_population
    b_tot = dataset.total_live_births
    
    if d_tot is None and dataset.mortality_schedule is not None and "deaths" in dataset.mortality_schedule.columns:
        d_tot = float(dataset.mortality_schedule["deaths"].sum())
        
    # 1. CDR
    cdr_val = None
    if d_tot is not None and t_pop is not None:
        cdr_res = calculate_crude_death_rate(d_tot, t_pop)
        results["CDR"] = cdr_res
        cdr_val = cdr_res.raw_value
        
    # 2. Corrected CDR (Fix B2: separate census coverage and death completeness)
    if cdr_val is not None:
        c_census = dataset.census_coverage_rate or (1.0 - dataset.pec_omission_rate if dataset.pec_omission_rate else None)
        c_death = dataset.death_registration_completeness
        
        # Only compute if at least one correction factor is provided
        if c_census is not None or c_death is not None:
            results["CORRECTED_CDR"] = calculate_corrected_cdr(
                crude_death_rate=cdr_val,
                death_registration_completeness=c_death or 1.0,
                census_coverage_rate=c_census or 1.0,
            )
            
    # 3. NMR
    if dataset.neonatal_deaths is not None and b_tot is not None and b_tot > 0:
        results["NMR"] = calculate_neonatal_mortality_rate(dataset.neonatal_deaths, b_tot)
        
    # 4. ENMR
    if dataset.early_neonatal_deaths is not None and b_tot is not None and b_tot > 0:
        results["ENMR"] = calculate_early_neonatal_mortality_rate(dataset.early_neonatal_deaths, b_tot)
        
    # 5. PNMR
    if dataset.infant_deaths is not None and dataset.neonatal_deaths is not None and b_tot is not None and b_tot > 0:
        results["PNMR"] = calculate_post_neonatal_mortality_rate(dataset.infant_deaths, dataset.neonatal_deaths, b_tot)
        
    # 6. IMR
    if dataset.infant_deaths is not None and b_tot is not None and b_tot > 0:
        results["IMR"] = calculate_infant_mortality_rate(dataset.infant_deaths, b_tot)
        
    # 7. CDR 1-4
    if dataset.child_deaths_1_4 is not None and dataset.pop_1_4 is not None and dataset.pop_1_4 > 0:
        results["CMR"] = calculate_child_mortality_rate(
            child_deaths_1_4=dataset.child_deaths_1_4,
            pop_1_4=dataset.pop_1_4,
        )
        
    # 8. U5MR
    if dataset.infant_deaths is not None and dataset.child_deaths_1_4 is not None and b_tot is not None and b_tot > 0:
        results["U5MR"] = calculate_under_5_mortality_rate(
            under_5_deaths=dataset.infant_deaths + dataset.child_deaths_1_4,
            total_live_births=b_tot,
        )
        
    # 9. MMR
    if dataset.maternal_deaths is not None and b_tot is not None and b_tot > 0:
        results["MMR"] = calculate_maternal_mortality_ratio(dataset.maternal_deaths, b_tot)
        
    # 10. ASDR, DSDR, SMR, ISDR
    if dataset.mortality_schedule is not None and not dataset.mortality_schedule.empty:
        asdr_res, mort_df = calculate_age_specific_death_rates(dataset.mortality_schedule)
        results["ASDR"] = asdr_res
        
        # Direct Standardization (Fix B4)
        try:
            dsdr_res = calculate_direct_standardized_rate(mort_df, dataset.standard_population)
            results["DSDR"] = dsdr_res
        except Exception:
            pass
            
        # Indirect Standardization & SMR (Fix B1)
        if d_tot is not None:
            try:
                smr_res, isdr_res = calculate_smr_and_indirect_standardized_rate(
                    observed_deaths=d_tot,
                    mortality_schedule=mort_df,
                    standard_population=dataset.standard_population,
                    standard_rates=dataset.standard_rates,
                    use_who_standard_reference=True,
                )
                results["SMR"] = smr_res
                results["ISDR"] = isdr_res
            except Exception:
                pass
                
    return results
