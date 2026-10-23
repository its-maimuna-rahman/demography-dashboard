"""
Data Quality Module: Demographic Quality Checks & Census Accuracy Audits
Implements:
1. Whipple's Index (Age heaping on 0 and 5, evaluated for Total, Male, and Female)
2. Myers' Blended Index (Digit preference across 0 to 9, with parameter-driven start_age and end_age)
3. Age Ratio Score (ARS) & Sex Ratio Score (SRS)
4. United Nations Age-Sex Accuracy (Joint) Index (UNAI)
5. Post-Enumeration Check (PEC) / Dual System Estimation (Chandra Sekar & Deming 1949)
6. Dual-record vital registration completeness
7. Dynamic Schema & Completeness Validator

References:
- United Nations (1955). Manual II: Methods of Appraisal of Quality of Basic Data for Population Estimates.
- Myers, R. J. (1940). Errors and Bias in the Reporting of Ages in Census Data. Transactions of the Actuarial Society of America.
- Chandra Sekar, C., & Deming, W. E. (1949). On a Method of Estimating Birth and Death Rates and the Extent of Registration. JASA, 44(245):101-115.
- Shryock, H. S., & Siegel, J. S. (1976). The Methods and Materials of Demography, Ch. 8.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple, Set
import numpy as np
import pandas as pd

from engine.base import QualityCheckResult, DemographicDataset
from engine.registry import MEASURES_CATALOGUE


def calculate_whipples_index(
    single_year_df: pd.DataFrame,
    age_col: str = "age",
    pop_col: str = "total",
    start_age: int = 23,
    end_age: int = 62,
) -> QualityCheckResult:
    """
    Calculate Whipple's Index for age heaping on terminal digits 0 and 5 (Fix B21).
    Evaluates Total, Male, and Female distributions where available.
    
    Formula:
    W = ( sum(P_x for x in 25, 30, ..., 60) / ( 0.20 * sum(P_y for y in 23..62) ) ) * 100
    """
    df = single_year_df.copy()
    if age_col not in df.columns:
        return QualityCheckResult(
            check_code="WHIPPLE",
            name="Whipple's Index (Age Heaping on 0 & 5)",
            score=None,
            status="MISSING_DATA",
            summary="Single-year age column not found.",
            interpretation="Single-year age distribution (ages 23–62) is required to evaluate Whipple's Index.",
            recommendation="Supply single-year age data from 23 to 62."
        )
        
    if pop_col not in df.columns:
        if "male" in df.columns and "female" in df.columns:
            df["total"] = df["male"] + df["female"]
            pop_col = "total"
        else:
            return QualityCheckResult(
                check_code="WHIPPLE",
                name="Whipple's Index (Age Heaping on 0 & 5)",
                score=None,
                status="MISSING_DATA",
                summary="Population count column not found.",
                interpretation="Population counts are required to compute Whipple's Index.",
                recommendation="Provide population column."
            )
            
    filtered = df[(df[age_col] >= start_age) & (df[age_col] <= end_age)]
    expected_count = end_age - start_age + 1
    has_gaps = len(filtered) < expected_count
    
    total_23_62 = filtered[pop_col].sum()
    if total_23_62 <= 0:
        return QualityCheckResult(
            check_code="WHIPPLE",
            name="Whipple's Index (Age Heaping on 0 & 5)",
            score=None,
            status="MISSING_DATA",
            summary="Zero population recorded in age span 23-62.",
            interpretation="Insufficient data to compute Whipple's Index.",
            recommendation="Verify population counts for ages 23 to 62."
        )
        
    fives_and_zeros = filtered[filtered[age_col] % 5 == 0][pop_col].sum()
    whipple_score = (fives_and_zeros / (0.20 * total_23_62)) * 100.0
    
    # Calculate for male and female if present
    whipple_male = None
    whipple_female = None
    if "male" in filtered.columns and filtered["male"].sum() > 0:
        tot_m = filtered["male"].sum()
        fz_m = filtered[filtered[age_col] % 5 == 0]["male"].sum()
        whipple_male = float((fz_m / (0.20 * tot_m)) * 100.0)
    if "female" in filtered.columns and filtered["female"].sum() > 0:
        tot_f = filtered["female"].sum()
        fz_f = filtered[filtered[age_col] % 5 == 0]["female"].sum()
        whipple_female = float((fz_f / (0.20 * tot_f)) * 100.0)
        
    # Scale categorization
    if whipple_score < 105.0:
        status = "EXCELLENT"
        interp = f"Highly accurate age reporting (Index = {whipple_score:.1f}, negligible preference on digits 0 and 5)."
        recom = "Data is robust for single-year actuarial and life table calculations."
    elif whipple_score < 110.0:
        status = "ACCEPTABLE"
        interp = f"Fairly accurate data (Index = {whipple_score:.1f}) with minor digit attraction."
        recom = "Standard demographic analysis is reliable; optional 5-year grouping."
    elif whipple_score < 125.0:
        status = "WARNING"
        interp = f"Approximate data (Index = {whipple_score:.1f}) showing noticeable clustering around digits 0 and 5."
        recom = "Apply Sprague or Beers 5-year graduated multipliers before single-year cohort projection."
    elif whipple_score < 175.0:
        status = "SEVERE"
        interp = f"Rough data (Index = {whipple_score:.1f}) with substantial age heaping and digit attraction."
        recom = "Aggregate into 5-year groups and apply Carrier-Farrag or Feeney smoothing."
    else:
        status = "SEVERE"
        interp = f"Very rough data (Index = {whipple_score:.1f}) exhibiting massive age distortion and clustering on 0 and 5."
        recom = "Direct single-year rates cannot be used; rigorous smoothing and PEC adjustments mandatory."
        
    if has_gaps:
        interp += f" [Warning: Detected {expected_count - len(filtered)} missing age single-year records in span {start_age}–{end_age}]."
        
    return QualityCheckResult(
        check_code="WHIPPLE",
        name="Whipple's Index (Age Heaping on 0 & 5)",
        score=float(whipple_score),
        status=status,
        summary=f"Whipple's Index = {whipple_score:.2f} ({status.title()})",
        interpretation=interp,
        recommendation=recom,
        details={
            "score": float(whipple_score),
            "whipple_male": whipple_male,
            "whipple_female": whipple_female,
            "start_age": start_age,
            "end_age": end_age,
            "population_23_62": float(total_23_62),
            "population_ending_0_5": float(fives_and_zeros),
            "has_missing_ages": has_gaps,
        }
    )


def calculate_myers_blended_index(
    single_year_df: pd.DataFrame,
    age_col: str = "age",
    pop_col: str = "total",
    start_age: int = 10,
    end_age: int = 69,
) -> QualityCheckResult:
    """
    Calculate Myers' Blended Index across all terminal digits 0 to 9 (Fix B8).
    Properly utilizes the passed start_age and end_age parameters.
    
    Method:
    1. Sum populations by terminal digit for ages start_age .. end_age (Sum 1).
    2. Sum populations by terminal digit for ages (start_age + 10) .. end_age (Sum 2).
    3. Blended count for digit d: (d+1) * Sum1 + (9-d) * Sum2.
    4. Calculate percentage distribution across digits 0-9.
    5. Myers' Index = 0.5 * sum( |%_d - 10.0%| ). Range: 0 (perfect) to 90 (all reported at one digit).
    """
    df = single_year_df.copy()
    if age_col not in df.columns or pop_col not in df.columns:
        if pop_col == "total" and "male" in df.columns and "female" in df.columns:
            df["total"] = df["male"] + df["female"]
        else:
            return QualityCheckResult(
                check_code="MYERS",
                name="Myers' Blended Index (Digits 0–9)",
                score=None,
                status="MISSING_DATA",
                summary="Single-year age distribution not provided.",
                interpretation="Single-year age data required to compute Myers' Blended Index.",
                recommendation=f"Provide single-year population data for age span {start_age} to {end_age}."
            )
            
    filtered = df[(df[age_col] >= start_age) & (df[age_col] <= end_age)]
    if filtered.empty or filtered[pop_col].sum() <= 0:
        return QualityCheckResult(
            check_code="MYERS",
            name="Myers' Blended Index (Digits 0–9)",
            score=None,
            status="MISSING_DATA",
            summary=f"Zero population recorded in age span {start_age}–{end_age}.",
            interpretation="Insufficient data to compute Myers' Index.",
            recommendation="Verify single-year population counts."
        )
        
    # Sum 1: Ages start_age .. end_age by terminal digit
    df_sum1 = df[(df[age_col] >= start_age) & (df[age_col] <= end_age)].copy()
    df_sum1["digit"] = df_sum1[age_col] % 10
    sum1 = df_sum1.groupby("digit")[pop_col].sum().to_dict()
    
    # Sum 2: Ages (start_age + 10) .. end_age by terminal digit
    second_start = start_age + 10
    df_sum2 = df[(df[age_col] >= second_start) & (df[age_col] <= end_age)].copy()
    df_sum2["digit"] = df_sum2[age_col] % 10
    sum2 = df_sum2.groupby("digit")[pop_col].sum().to_dict()
    
    blended_counts = {}
    for d in range(10):
        s1 = sum1.get(d, 0.0)
        s2 = sum2.get(d, 0.0)
        w1 = d + 1
        w2 = 9 - d
        blended_counts[d] = (w1 * s1) + (w2 * s2)
        
    total_blended = sum(blended_counts.values())
    if total_blended <= 0:
        return QualityCheckResult(
            check_code="MYERS",
            name="Myers' Blended Index (Digits 0–9)",
            score=None,
            status="MISSING_DATA",
            summary="Blended population sum is zero.",
            interpretation="Cannot compute Myers' Index.",
            recommendation="Check data inputs."
        )
        
    blended_pct = {d: (cnt / total_blended) * 100.0 for d, cnt in blended_counts.items()}
    deviations = {d: abs(pct - 10.0) for d, pct in blended_pct.items()}
    myers_index = 0.5 * sum(deviations.values())
    
    max_digit = max(blended_pct, key=blended_pct.get)
    min_digit = min(blended_pct, key=blended_pct.get)
    
    if myers_index < 5.0:
        status = "EXCELLENT"
        interp = f"Very low digit preference (Myers' Index = {myers_index:.2f}). Age reporting across digits 0–9 is highly accurate."
        recom = "High confidence in single-year demographic modeling and projections."
    elif myers_index < 10.0:
        status = "ACCEPTABLE"
        interp = f"Moderate digit preference (Myers' Index = {myers_index:.2f}). Preferred digit: '{max_digit}' ({blended_pct[max_digit]:.1f}% vs 10% expected)."
        recom = "Standard 5-year groupings recommended for precision analysis."
    elif myers_index < 20.0:
        status = "WARNING"
        interp = f"Substantial digit preference (Myers' Index = {myers_index:.2f}). Heavy attraction to digit '{max_digit}'."
        recom = "Graduation techniques (Sprague or Beers) required before demographic inference."
    else:
        status = "SEVERE"
        interp = f"Severe age heaping (Myers' Index = {myers_index:.2f}). Extreme distortion around digit '{max_digit}' ({blended_pct[max_digit]:.1f}% vs 10% expected)."
        recom = "Single-year data should not be used directly; apply strong mathematical graduation."
        
    return QualityCheckResult(
        check_code="MYERS",
        name="Myers' Blended Index (Digits 0–9)",
        score=float(myers_index),
        status=status,
        summary=f"Myers' Index = {myers_index:.2f} ({status.title()})",
        interpretation=interp,
        recommendation=recom,
        details={
            "score": float(myers_index),
            "start_age": start_age,
            "end_age": end_age,
            "digit_distribution_pct": blended_pct,
            "digit_deviations": deviations,
            "most_preferred_digit": max_digit,
            "most_avoided_digit": min_digit,
        }
    )


def calculate_un_joint_score(
    age_group_5yr_df: pd.DataFrame,
) -> QualityCheckResult:
    """
    Calculate United Nations Age-Sex Accuracy (Joint) Index (UNAI).
    UN Joint Score = 3 * Sex Ratio Score (SRS) + Age Ratio Score Male (ARS_M) + Age Ratio Score Female (ARS_F)
    
    UN Thresholds:
    - < 20: Accurate
    - 20 - 40: Inaccurate
    - > 40: Highly Inaccurate
    """
    df = age_group_5yr_df.copy()
    if "male" not in df.columns or "female" not in df.columns:
        return QualityCheckResult(
            check_code="UN_JOINT_SCORE",
            name="UN Age-Sex Accuracy (Joint) Index",
            score=None,
            status="MISSING_DATA",
            summary="Male and female 5-year age groups required.",
            interpretation="Cannot compute UN Joint Score without sex-disaggregated 5-year age counts.",
            recommendation="Provide 5-year age table with male and female columns."
        )
        
    males = df["male"].values
    females = df["female"].values
    n = len(df)
    if n < 4:
        return QualityCheckResult(
            check_code="UN_JOINT_SCORE",
            name="UN Age-Sex Accuracy (Joint) Index",
            score=None,
            status="MISSING_DATA",
            summary="At least 4 consecutive 5-year age groups required.",
            interpretation="Insufficient age groups to calculate UN Joint Score.",
            recommendation="Provide standard 5-year age distribution."
        )
        
    # Sex ratios: males per 100 females
    sr_vals = np.where(females > 0, (males / females) * 100.0, 100.0)
    # Sex Ratio Score (SRS): mean absolute successive difference
    srs = float(np.mean(np.abs(np.diff(sr_vals))))
    
    # Age Ratio Scores (ARS): deviation of age group from average of adjacent groups
    def calc_ars(pop_series: np.ndarray) -> float:
        devs = []
        for i in range(1, len(pop_series) - 1):
            denom = pop_series[i - 1] + pop_series[i + 1]
            if denom > 0:
                age_ratio = (2.0 * pop_series[i] / denom) * 100.0
                devs.append(abs(age_ratio - 100.0))
        return float(np.mean(devs)) if devs else 0.0
        
    ars_male = calc_ars(males)
    ars_female = calc_ars(females)
    
    un_joint_score = 3.0 * srs + ars_male + ars_female
    
    if un_joint_score < 20.0:
        status = "EXCELLENT"
        interp = f"Accurate age-sex reporting (UN Joint Score = {un_joint_score:.1f} < 20)."
        recom = "Reliable for detailed cohort analysis without prior smoothing."
    elif un_joint_score <= 40.0:
        status = "WARNING"
        interp = f"Inaccurate age-sex reporting (UN Joint Score = {un_joint_score:.1f}, between 20 and 40)."
        recom = "Smoothing of 5-year age structure recommended before cohort projection."
    else:
        status = "SEVERE"
        interp = f"Highly inaccurate age-sex reporting (UN Joint Score = {un_joint_score:.1f} > 40)."
        recom = "Extensive graduation, smoothing, and demographic reconstruction required."
        
    return QualityCheckResult(
        check_code="UN_JOINT_SCORE",
        name="UN Age-Sex Accuracy (Joint) Index",
        score=float(un_joint_score),
        status=status,
        summary=f"UN Joint Index = {un_joint_score:.1f} ({status.title()})",
        interpretation=interp,
        recommendation=recom,
        details={
            "un_joint_score": float(un_joint_score),
            "sex_ratio_score": float(srs),
            "age_ratio_score_male": float(ars_male),
            "age_ratio_score_female": float(ars_female),
        }
    )


def calculate_pec_comparison(
    census_count: float,
    pec_count: Optional[float] = None,
    matched_count: Optional[float] = None,
    omission_rate: Optional[float] = None,
    name: str = "Post-Enumeration Check (PEC) Coverage Analysis",
) -> QualityCheckResult:
    """
    Evaluate Census Coverage & Completeness using Post-Enumeration Check (PEC)
    or Dual System Estimation (DSE) (Chandra Sekar & Deming 1949 formula).
    
    Citation: Chandra Sekar, C., & Deming, W. E. (1949). JASA, 44(245):101-115.
    """
    if omission_rate is not None:
        omission_pct = omission_rate * 100.0
        comp_rate = 1.0 - omission_rate
        est_true_pop = census_count / comp_rate if comp_rate > 0 else census_count
        method = "Direct Net Omission Rate Parameter"
    elif pec_count is not None and matched_count is not None and matched_count > 0:
        est_true_pop = (census_count * pec_count) / matched_count
        omission_rate = (est_true_pop - census_count) / est_true_pop if est_true_pop > 0 else 0.0
        omission_pct = omission_rate * 100.0
        comp_rate = census_count / est_true_pop if est_true_pop > 0 else 1.0
        method = "Chandra Sekar & Deming (1949) Dual System Estimation"
    else:
        return QualityCheckResult(
            check_code="PEC",
            name=name,
            score=None,
            status="MISSING_DATA",
            summary="PEC survey or omission factor not provided.",
            interpretation="Census coverage completeness cannot be independently benchmarked.",
            recommendation="Provide PEC survey sample counts or net omission rate to calculate corrected vital rates."
        )
        
    net_undercount = est_true_pop - census_count
    
    if omission_pct < 2.0:
        status = "EXCELLENT"
        interp = f"Exceptional census coverage ({comp_rate*100:.1f}% completeness, {omission_pct:.2f}% net undercount)."
        recom = "Unadjusted census figures are highly reliable for population baselines."
    elif omission_pct < 5.0:
        status = "ACCEPTABLE"
        interp = f"Acceptable coverage ({comp_rate*100:.1f}% completeness, {omission_pct:.2f}% net undercount)."
        recom = f"Apply PEC coverage adjustment factor k = {1/comp_rate:.4f} for precision denominators."
    elif omission_pct < 10.0:
        status = "WARNING"
        interp = f"Moderate undercount ({omission_pct:.2f}% net omission, ~{net_undercount:,.0f} omitted persons)."
        recom = "Corrected death and birth rates mandatory to avoid deflated vital rates."
    else:
        status = "SEVERE"
        interp = f"Severe under-enumeration ({omission_pct:.2f}% net omission). Substantial coverage failure."
        recom = "Full demographic re-weighting and synthetic cohort reconstruction mandatory."
        
    return QualityCheckResult(
        check_code="PEC",
        name=name,
        score=float(omission_pct),
        status=status,
        summary=f"Net Undercount = {omission_pct:.2f}% (Completeness: {comp_rate*100:.1f}%)",
        interpretation=interp,
        recommendation=recom,
        details={
            "census_count": float(census_count),
            "estimated_true_population": float(est_true_pop),
            "net_undercount_persons": float(net_undercount),
            "completeness_rate": float(comp_rate),
            "omission_rate": float(omission_rate),
            "adjustment_factor_k": float(1.0 / comp_rate) if comp_rate > 0 else 1.0,
            "method": method,
            "citation": "Chandra Sekar, C., & Deming, W. E. (1949). JASA, 44(245):101-115",
        }
    )


def validate_dataset_completeness(dataset: DemographicDataset) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """
    Inspects dataset against the central measures catalogue dynamically (Fix B11 & B12).
    Returns:
    - computable_measures: List of measure codes that CAN be calculated.
    - missing_measures: List of measure codes that CANNOT be calculated.
    - gap_analysis: Structured report of missing fields, why they matter, and guidance.
    """
    computable: List[str] = []
    missing: List[str] = []
    gap_analysis: Dict[str, Any] = {}
    
    # Population totals
    has_m = dataset.male_population is not None or (dataset.single_year_ages is not None and "male" in dataset.single_year_ages.columns)
    has_f = dataset.female_population is not None or (dataset.single_year_ages is not None and "female" in dataset.single_year_ages.columns)
    has_t = dataset.total_population is not None or (has_m and has_f)
    
    # 1. Sex Composition
    if has_m and has_t:
        computable.append("MP")
    else:
        missing.append("MP")
        gap_analysis["MP"] = {"missing_fields": ["male_population", "total_population"], "reason": "Requires male population and total population."}
        
    if has_m and has_f:
        computable.extend(["SR", "EXCESS_M"])
    else:
        missing.extend(["SR", "EXCESS_M"])
        gap_analysis["SR"] = {"missing_fields": ["male_population", "female_population"], "reason": "Requires sex-disaggregated counts."}
        
    if dataset.male_births is not None and dataset.female_births is not None:
        computable.append("SRB")
    else:
        missing.append("SRB")
        
    # 2. Age & Dependency
    p0_14 = dataset.pop_0_14
    p15_64 = dataset.pop_15_64
    p65p = dataset.pop_65_plus
    has_broad = (p0_14 is not None and p15_64 is not None and p65p is not None) or (dataset.age_group_5yr is not None) or (dataset.single_year_ages is not None)
    
    if has_broad:
        computable.extend(["ACR", "TDR", "CDR_CHILD", "OADR", "AI", "PSR"])
    else:
        missing.extend(["ACR", "TDR", "CDR_CHILD", "OADR", "AI", "PSR"])
        gap_analysis["Age_Structure"] = {"missing_fields": ["pop_0_14", "pop_15_64", "pop_65_plus"], "reason": "Requires broad functional age groups or age table."}
        
    if dataset.single_year_ages is not None or dataset.age_group_5yr is not None:
        computable.append("MEDIAN_AGE")
    else:
        missing.append("MEDIAN_AGE")
        
    if dataset.area_km2 is not None and has_t:
        computable.append("DENSITY")
    else:
        missing.append("DENSITY")
        
    # 3. Fertility
    has_births = dataset.total_live_births is not None
    if has_births and has_t:
        computable.append("CBR")
    else:
        missing.append("CBR")
        
    w15_49 = dataset.total_women_15_49 or (dataset.fertility_schedule is not None and "female_pop" in dataset.fertility_schedule.columns)
    if has_births and w15_49:
        computable.append("GFR")
    else:
        missing.append("GFR")
        
    if dataset.marital_births is not None and dataset.married_women_15_49 is not None:
        computable.append("MBR")
    else:
        missing.append("MBR")
        
    if dataset.fertility_schedule is not None and "female_pop" in dataset.fertility_schedule.columns and "births" in dataset.fertility_schedule.columns:
        computable.extend(["ASFR", "TFR", "GRR", "MAC"])
        # NRR requires life table or mortality schedule
        if dataset.mortality_schedule is not None or dataset.life_table_female is not None:
            computable.append("NRR")
        else:
            missing.append("NRR")
    else:
        missing.extend(["ASFR", "TFR", "GRR", "NRR", "MAC"])
        
    # 4. Mortality
    has_deaths = dataset.total_deaths is not None or (dataset.mortality_schedule is not None and "deaths" in dataset.mortality_schedule.columns)
    if has_deaths and has_t:
        computable.append("CDR")
    else:
        missing.append("CDR")
        
    if has_deaths and (dataset.census_coverage_rate is not None or dataset.death_registration_completeness is not None or dataset.pec_omission_rate is not None):
        computable.append("CORRECTED_CDR")
    else:
        missing.append("CORRECTED_CDR")
        
    if dataset.neonatal_deaths is not None and has_births:
        computable.append("NMR")
    else:
        missing.append("NMR")
        
    if dataset.infant_deaths is not None and has_births:
        computable.append("IMR")
    else:
        missing.append("IMR")
        
    if (dataset.child_deaths_1_4 is not None and dataset.pop_1_4 is not None) or (dataset.infant_deaths is not None and dataset.child_deaths_1_4 is not None and has_births):
        computable.append("CMR")
    else:
        missing.append("CMR")
        
    if dataset.mortality_schedule is not None and "population" in dataset.mortality_schedule.columns and "deaths" in dataset.mortality_schedule.columns:
        computable.extend(["ASDR", "DSDR", "E0", "E65", "45Q15"])
        if dataset.standard_population is not None or dataset.standard_rates is not None:
            computable.extend(["SMR", "ISDR"])
        else:
            missing.extend(["SMR", "ISDR"])
    else:
        missing.extend(["ASDR", "DSDR", "SMR", "ISDR", "E0", "E65", "45Q15"])
        
    # 5. Nuptiality
    if dataset.marital_status_df is not None and not dataset.marital_status_df.empty:
        computable.extend(["SMAM_FEMALE", "SMAM_MALE", "SPOUSAL_GAP", "CELIBACY"])
    else:
        missing.extend(["SMAM_FEMALE", "SMAM_MALE", "SPOUSAL_GAP", "CELIBACY"])
        
    if dataset.marriages_total is not None and has_t:
        computable.append("CMRG")
    else:
        missing.append("CMRG")
        
    if dataset.divorces_total is not None and has_t:
        computable.extend(["CDVR", "GDVR"])
    else:
        missing.extend(["CDVR", "GDVR"])
        
    # 6. Migration
    if dataset.in_migrants is not None and dataset.out_migrants is not None and has_t:
        computable.extend(["NMRG", "MER"])
    else:
        missing.extend(["NMRG", "MER"])
        
    return computable, missing, gap_analysis


def run_all_quality_checks(dataset: DemographicDataset) -> Dict[str, QualityCheckResult]:
    """Runs all data-quality validations on the provided dataset."""
    results: Dict[str, QualityCheckResult] = {}
    
    # 1. Whipple's Index (Total, Male, Female)
    if dataset.single_year_ages is not None and not dataset.single_year_ages.empty:
        results["WHIPPLE"] = calculate_whipples_index(dataset.single_year_ages)
    else:
        results["WHIPPLE"] = QualityCheckResult(
            check_code="WHIPPLE",
            name="Whipple's Index (Age Heaping on 0 & 5)",
            score=None,
            status="MISSING_DATA",
            summary="Single-year age distribution not provided.",
            interpretation="Cannot evaluate Whipple's Index without single-year age data.",
            recommendation="Upload a single-year age table (ages 23–62) to assess digit preference on 0 and 5."
        )
        
    # 2. Myers' Blended Index
    if dataset.single_year_ages is not None and not dataset.single_year_ages.empty:
        results["MYERS"] = calculate_myers_blended_index(dataset.single_year_ages, start_age=10, end_age=69)
    else:
        results["MYERS"] = QualityCheckResult(
            check_code="MYERS",
            name="Myers' Blended Index (Digits 0–9)",
            score=None,
            status="MISSING_DATA",
            summary="Single-year age distribution not provided.",
            interpretation="Cannot evaluate Myers' digit attraction without single-year age data.",
            recommendation="Upload single-year age distribution to compute full 10-digit preference index."
        )
        
    # 3. UN Age-Sex Accuracy Joint Score
    if dataset.age_group_5yr is not None and not dataset.age_group_5yr.empty:
        results["UN_JOINT_SCORE"] = calculate_un_joint_score(dataset.age_group_5yr)
    elif dataset.single_year_ages is not None and not dataset.single_year_ages.empty:
        # Build 5-year table from single years
        sy = dataset.single_year_ages
        grps = []
        for a in range(0, 85, 5):
            sub = sy[(sy["age"] >= a) & (sy["age"] <= a + 4)]
            grps.append({
                "age_group": f"{a}-{a+4}",
                "male": sub["male"].sum() if "male" in sub.columns else sub["total"].sum() * 0.5,
                "female": sub["female"].sum() if "female" in sub.columns else sub["total"].sum() * 0.5,
            })
        results["UN_JOINT_SCORE"] = calculate_un_joint_score(pd.DataFrame(grps))
    else:
        results["UN_JOINT_SCORE"] = QualityCheckResult(
            check_code="UN_JOINT_SCORE",
            name="UN Age-Sex Accuracy (Joint) Index",
            score=None,
            status="MISSING_DATA",
            summary="5-year age-sex distribution not provided.",
            interpretation="Requires 5-year age groups disaggregated by sex.",
            recommendation="Provide 5-year age counts for males and females."
        )
        
    # 4. PEC Post-Enumeration Check
    t_pop = dataset.total_population
    if t_pop is None and dataset.single_year_ages is not None:
        tot_col = "total" if "total" in dataset.single_year_ages.columns else dataset.single_year_ages.columns[1]
        t_pop = float(dataset.single_year_ages[tot_col].sum())
        
    omission = dataset.pec_omission_rate
    if omission is None and dataset.census_coverage_rate is not None:
        omission = 1.0 - dataset.census_coverage_rate
        
    if t_pop is not None and omission is not None:
        results["PEC"] = calculate_pec_comparison(
            census_count=t_pop,
            omission_rate=omission,
        )
    else:
        results["PEC"] = QualityCheckResult(
            check_code="PEC",
            name="Post-Enumeration Check (PEC) Coverage",
            score=None,
            status="MISSING_DATA",
            summary="No PEC or omission rate specified.",
            interpretation="Assuming standard unadjusted enumeration baseline.",
            recommendation="Specify PEC omission rate or completeness percentage to adjust crude rates."
        )
        
    # 5. Schema Completeness Check (Dynamic Measure Counts, Fix B11)
    comp, miss, gaps = validate_dataset_completeness(dataset)
    total_eval = len(comp) + len(miss)
    comp_pct = (len(comp) / total_eval * 100.0) if total_eval > 0 else 0.0
    status_str = "EXCELLENT" if comp_pct >= 90 else ("ACCEPTABLE" if comp_pct >= 60 else ("WARNING" if comp_pct >= 30 else "SEVERE"))
    
    results["SCHEMA_CHECK"] = QualityCheckResult(
        check_code="SCHEMA_CHECK",
        name="Dataset Completeness & Measure Readiness",
        score=comp_pct,
        status=status_str,
        summary=f"{len(comp)}/{total_eval} indicators computable ({comp_pct:.0f}% readiness)",
        interpretation=f"Dataset contains sufficient inputs to evaluate {len(comp)} demographic indicators across core syllabus blocks. {len(miss)} indicators require supplemental inputs.",
        recommendation="Download and populate section CSV templates to unlock remaining indicators.",
        details={
            "computable_count": len(comp),
            "computable_measures": comp,
            "missing_count": len(miss),
            "missing_measures": miss,
            "total_catalogue_count": total_eval,
            "gap_analysis": gaps,
        }
    )
    
    return results
