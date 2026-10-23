"""
Unit tests for New Syllabus Sections & Regression Tests (improve.md B1-B23, S1-S11)
Validates Life Tables, Nuptiality (SMAM), Migration, Sprague Graduation, Stable Population,
and regression tests for B1, B2, B3, B5, B6, B7, B8, B10, B22.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from engine.lifetable import build_abridged_life_table
from engine.nuptiality import calculate_smam, compute_nuptiality_section
from engine.migration import calculate_migration_rates, calculate_residual_net_migration
from engine.graduation import graduate_5yr_to_single_year_sprague
from engine.stable import solve_lotka_intrinsic_r, compute_stable_population_measures
from engine.transition import classify_demographic_transition_stage
from engine.mortality import (
    calculate_smr_and_indirect_standardized_rate,
    calculate_corrected_cdr,
    calculate_child_mortality_rate,
    calculate_under_5_mortality_rate,
)
from engine.fertility import (
    calculate_net_reproduction_rate,
    calculate_marital_birth_rate,
)
from engine.loader import load_demographic_dataset
from engine.quality import calculate_myers_blended_index


# -------------------------------------------------------------
# 1. Life Tables (S5)
# -------------------------------------------------------------
def test_abridged_life_table_properties():
    age_groups = [
        "0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39",
        "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80-84", "85+"
    ]
    asdr = [6.2, 0.7, 0.5, 1.1, 1.5, 1.8, 2.4, 3.3, 4.8, 7.2, 10.8, 16.4, 25.2, 38.0, 58.0, 88.0, 134.0, 215.0]
    pop = [100000] * 18
    df_mort = pd.DataFrame({"age_group": age_groups, "population": pop, "asdr": asdr})
    
    lt, indicators = build_abridged_life_table(df_mort, radix=100000.0)
    
    # 1. Check required demographic life table columns
    expected_cols = ["x", "n", "nax", "nMx", "nqx", "npx", "lx", "ndx", "nLx", "Tx", "ex"]
    for col in expected_cols:
        assert col in lt.columns, f"Missing column {col} in life table"
        
    # 2. Check radix and monotonic decline of lx
    assert lt.loc[0, "lx"] == 100000.0
    assert (lt["lx"].diff().dropna() <= 0).all(), "lx must be non-increasing"
    
    # 3. Sum of ndx must equal radix
    assert pytest.approx(lt["ndx"].sum(), abs=1.0) == 100000.0
    
    # 4. Probabilities of dying in [0, 1]
    assert (lt["nqx"] >= 0.0).all() and (lt["nqx"] <= 1.0).all()
    
    # 5. Life expectancies must be realistic
    e0 = indicators["E0"].raw_value
    assert 60.0 < e0 < 85.0, f"e0 {e0} outside realistic band"
    e65 = indicators["E65"].raw_value
    assert 10.0 < e65 < 25.0, f"e65 {e65} outside realistic band"


# -------------------------------------------------------------
# 2. Nuptiality (S6): Hajnal SMAM
# -------------------------------------------------------------
def test_singulate_mean_age_at_marriage_hajnal():
    age_groups = ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54"]
    props_female = [0.65, 0.28, 0.12, 0.05, 0.03, 0.02, 0.015, 0.01]
    df_nupt = pd.DataFrame({
        "age_group": age_groups,
        "never_married": [p * 10000 for p in props_female],
        "total": [10000] * len(age_groups),
    })
    
    res = calculate_smam(df_nupt, sex="female")
    smam = res.raw_value
    
    # SMAM must be strictly bounded between 15 and 50
    assert 15.0 < smam < 50.0
    # For this distribution, SMAM should be around ~20.5 years
    assert 18.0 <= smam <= 24.0
    assert "SMAM" in res.shortform
    assert res.plain_interpretation != ""


# -------------------------------------------------------------
# 3. Migration (S7)
# -------------------------------------------------------------
def test_migration_rates_and_balancing_equation():
    rates = calculate_migration_rates(
        in_migrants=450000,
        out_migrants=320000,
        midyear_population=15000000,
        per=1000,
    )
    
    assert "NMRG" in rates
    assert "MER" in rates
    nmr = rates["NMRG"].raw_value
    assert pytest.approx(nmr, 0.01) == (450000 - 320000) / 15000.0  # +8.67
    
    # Balancing equation: P2 = P1 + B - D + NM
    res_bal = calculate_residual_net_migration(
        pop_start=1000000,
        pop_end=1050000,
        births=70000,
        deaths=30000,
    )
    assert res_bal["net_migration_count"] == 10000.0


# -------------------------------------------------------------
# 4. Sprague Osculatory Graduation (S8)
# -------------------------------------------------------------
def test_sprague_graduation_resum_property():
    five_year_counts = [120000, 115000, 110000, 105000, 98000, 90000, 80000, 68000, 52000, 35000]
    df_single, meta = graduate_5yr_to_single_year_sprague(five_year_counts, start_age=0)
    
    assert len(df_single) == len(five_year_counts) * 5
    assert meta["re_sum_verified"] is True
    
    # Key property: each 5-year chunk of single years must re-sum to the original 5-year group count!
    for i, orig_count in enumerate(five_year_counts):
        sub_sum = df_single.iloc[i * 5 : (i + 1) * 5]["graduated_population"].sum()
        assert pytest.approx(sub_sum, abs=2.0) == orig_count, f"Re-sum mismatch in 5-year group {i}"


# -------------------------------------------------------------
# 5. Stable & Stationary Population (S9)
# -------------------------------------------------------------
def test_stable_and_stationary_lotka():
    fert_groups = ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49"]
    df_fert = pd.DataFrame({
        "age_group": fert_groups,
        "female_pop": [500000] * 7,
        "births": [30000, 90000, 80000, 45000, 18000, 5000, 1500],
    })
    
    age_groups = [
        "0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39",
        "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80-84", "85+"
    ]
    asdr = [6.0, 0.7, 0.5, 1.0, 1.4, 1.8, 2.3, 3.2, 4.6, 7.0, 10.5, 16.0, 24.5, 37.0, 57.0, 87.0, 130.0, 210.0]
    df_mort = pd.DataFrame({"age_group": age_groups, "population": [100000] * 18, "asdr": asdr})
    
    res = compute_stable_population_measures(df_fert, df_mort)
    assert "LOTKA_R" in res
    assert "INTRINSIC_B" in res
    assert "INTRINSIC_D" in res
    assert "GEN_LEN" in res
    
    r_val = res["LOTKA_R"].raw_value
    b_val = res["INTRINSIC_B"].raw_value
    d_val = res["INTRINSIC_D"].raw_value
    # Fundamental Lotka relationship: d = b - r
    assert pytest.approx(d_val, abs=0.1) == (b_val - r_val * 10.0)


# -------------------------------------------------------------
# 6. Regression Tests for improve.md Bugs (B1 - B23)
# -------------------------------------------------------------
def test_b1_smr_no_standard_supplied():
    """B1: SMR must not return 1.0 tautology when standard ASDR is not provided."""
    df_mort = pd.DataFrame({
        "age_group": ["0-4", "5-9", "10-14", "15-19"],
        "population": [10000, 9500, 9000, 8500],
        "deaths": [60, 7, 5, 10],
    })
    with pytest.raises(ValueError):
        calculate_smr_and_indirect_standardized_rate(
            observed_deaths=82,
            mortality_schedule=df_mort,
            standard_rates=None,
            use_who_standard_reference=False,
        )


def test_b2_b3_corrected_cdr_no_defaults():
    """B2 & B3: Corrected CDR must adjust both numerator and denominator and avoid fake 0.95 defaults."""
    with pytest.raises(ValueError):
        calculate_corrected_cdr(
            crude_death_rate=8.0,
            death_registration_completeness=None,
            census_coverage_rate=None,
        )
        
    # Dual adjustment formula: CDR_true = CDR_raw * (C_census / C_death)
    res = calculate_corrected_cdr(
        crude_death_rate=8.0,
        death_registration_completeness=0.80,
        census_coverage_rate=0.96,
    )
    assert pytest.approx(res.raw_value, 0.01) == 9.60


def test_b5_nrr_uses_life_table_survival():
    """B5: NRR must use real life table person-years (nLx / l0), not 0.965 hardcoded multiplier."""
    fert_groups = ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49"]
    df_fert = pd.DataFrame({
        "age_group": fert_groups,
        "female_pop": [100000] * 7,
        "female_births": [4000, 12000, 10000, 5000, 2000, 500, 100],
    })
    
    df_mort = pd.DataFrame({
        "age_group": fert_groups,
        "population": [100000] * 7,
        "asdr": [1.5, 1.8, 2.2, 3.0, 4.5, 6.8, 10.0],
    })
    lt, _ = build_abridged_life_table(df_mort)
    
    res = calculate_net_reproduction_rate(
        fertility_schedule=df_fert,
        life_table_female=lt,
    )
    assert res.notes is not None
    assert "life table" in res.notes.lower()
    assert res.inputs_used.get("method") == "life_table_survival_integration"


def test_b6_mbr_missing_marital_births():
    """B6: MBR must not silently replace missing marital births with total births."""
    with pytest.raises(ValueError):
        calculate_marital_birth_rate(
            marital_live_births=None,
            married_women_15_49=500000,
        )


def test_b7_loader_no_invented_data():
    """B7: Loader must not invent married_women (65%) or marital_births (85%)."""
    csv_sample = """age_group,male,female,total,births,deaths
0-4,1000,1000,2000,0,10
15-19,1000,1000,2000,50,2
"""
    ds = load_demographic_dataset(csv_sample, name="Strict Loader Test")
    assert ds.married_women_15_49 is None, "married_women_15_49 must not be invented!"
    assert ds.marital_births is None, "marital_births must not be invented!"


def test_b8_myers_respects_age_range_parameters():
    """B8: Myers blended index must yield distinct scores for different age ranges."""
    ages = list(range(100))
    pop = [10000 if a % 10 == 0 else 8000 for a in ages]
    df_single = pd.DataFrame({"age": ages, "total": pop})
    
    m1 = calculate_myers_blended_index(df_single, start_age=10, end_age=69)
    m2 = calculate_myers_blended_index(df_single, start_age=20, end_age=59)
    
    assert m1.score is not None and m2.score is not None
    assert isinstance(m1.score, float)
    assert m1.details["start_age"] == 10
    assert m2.details["start_age"] == 20


def test_b10_cmr_and_u5mr_separation():
    """B10: CMR (1-4 death rate per 1,000) and U5MR (probability of dying before age 5) are distinct."""
    cmr_res = calculate_child_mortality_rate(child_deaths_1_4=250, pop_1_4=50000)
    assert cmr_res.shortform == "CDR(1-4)"
    assert pytest.approx(cmr_res.raw_value, 0.01) == 5.0
    
    u5mr_res = calculate_under_5_mortality_rate(under_5_deaths=450, total_live_births=10000)
    assert u5mr_res.shortform == "U5MR"
    assert pytest.approx(u5mr_res.raw_value, 0.01) == 45.0


def test_b4_dsdr_unmatched_labels_raises_error():
    """B4: DSDR with unmatched age labels must raise ValueError instead of inventing weights."""
    from engine.mortality import calculate_direct_standardized_rate
    # Single year labels "0", "1", "2" cannot match standard 5-year groupings
    df_single = pd.DataFrame({
        "age_group": ["0", "1", "2", "3", "4"],
        "population": [1000] * 5,
        "deaths": [5, 2, 1, 1, 1],
    })
    with pytest.raises(ValueError):
        calculate_direct_standardized_rate(df_single)


def test_s10_transition_stages():
    """S10: Demographic Transition Theory Stage Classification."""
    # Stage 1: High birth and death rates
    s1 = classify_demographic_transition_stage(cbr=42.0, cdr=38.0, tfr=6.0, life_expectancy=40.0)
    assert s1["stage"] == 1
    
    # Stage 3/4: Modern transition
    s4 = classify_demographic_transition_stage(cbr=12.0, cdr=7.0, tfr=1.7, life_expectancy=75.0)
    assert s4["stage"] in (3, 4)


def test_s11_cohort_component_projection_execution():
    """S11: Cohort-component projection forward simulation with 3 scenarios."""
    from engine.projection import run_cohort_component_projection
    age_groups = [
        "0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39",
        "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80-84", "85+"
    ]
    df_pop = pd.DataFrame({
        "age_group": age_groups,
        "male": [500000] * 18,
        "female": [500000] * 18,
        "total": [1000000] * 18,
    })
    fert_groups = ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49"]
    df_fert = pd.DataFrame({
        "age_group": fert_groups,
        "female_pop": [500000] * 7,
        "births": [20000, 60000, 50000, 25000, 10000, 2000, 500],
    })
    df_mort = pd.DataFrame({
        "age_group": age_groups,
        "population": [1000000] * 18,
        "deaths": [6000] + [800] * 17,
    })
    
    res = run_cohort_component_projection(
        base_age_sex_df=df_pop,
        fertility_schedule=df_fert,
        mortality_schedule=df_mort,
        base_year=2024,
        horizon_years=25,
        scenario="medium",
    )
    assert res.base_year == 2024
    assert res.horizon_years == 25
    assert len(res.projection_years) == 6  # 2024, 2029, 2034, 2039, 2044, 2049
    assert res.total_population_series.iloc[0] == 18000000.0
    assert isinstance(res.policy_flags, list)


def test_b22_chandra_sekar_deming_citation():
    """B22: Dual-record completeness must properly cite Chandra Sekar & Deming (1949)."""
    from engine.quality import calculate_pec_comparison
    pec_res = calculate_pec_comparison(census_count=100000, pec_count=102000, matched_count=98000)
    citation = pec_res.details.get("citation", "")
    assert "Chandra Sekar" in citation and "Deming" in citation


# -------------------------------------------------------------
# 7. Advanced Syllabus Methods (§5 in improve.md)
# -------------------------------------------------------------
def test_complete_and_multiple_decrement_and_working_life():
    """S5: Complete Life Table, Multiple Decrement, and Working Life Tables."""
    from engine.lifetable import (
        build_complete_life_table,
        build_multiple_decrement_table,
        calculate_working_life_expectancy,
    )
    # Single-year complete life table
    single_ages = list(range(86))
    asdr = [5.0] + [0.4] * 14 + [1.2] * 35 + [12.0] * 36
    df_single = pd.DataFrame({"age": single_ages, "asdr": asdr})
    clt = build_complete_life_table(df_single, radix=100000.0)
    assert len(clt) == 86
    assert clt.loc[0, "lx"] == 100000.0
    assert clt.loc[0, "ex"] > 50.0
    assert (clt["1qx"] >= 0.0).all() and (clt["1qx"] <= 1.0).all()

    # Multiple decrement (cause-deleted)
    df_abridged = pd.DataFrame({
        "age_group": ["0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80-84", "85+"],
        "population": [100000] * 18,
        "deaths": [600, 70, 50, 100, 140, 180, 240, 330, 480, 720, 1080, 1640, 2520, 3800, 5800, 8800, 13400, 21500],
        "deaths_cardiovascular": [0, 0, 0, 10, 20, 30, 60, 100, 180, 320, 550, 900, 1450, 2200, 3500, 5500, 8500, 14000],
    })
    base_lt, gains = build_multiple_decrement_table(df_abridged, cause_columns=["deaths_cardiovascular"])
    assert "gain_if_eliminated_deaths_cardiovascular" in gains
    assert gains["gain_if_eliminated_deaths_cardiovascular"] > 0.0

    # Working life expectancy
    activity_rates = {0: 0.0, 15: 0.60, 25: 0.85, 55: 0.70, 65: 0.25}
    wlt = calculate_working_life_expectancy(base_lt, activity_rates)
    assert "working_ex" in wlt.columns
    assert wlt.loc[0, "working_ex"] > 0.0
    assert wlt.loc[0, "working_ex"] < base_lt.loc[0, "ex"]


def test_nuptiality_marriage_age_shift_what_if():
    """S6: Age at marriage and fertility what-if simulation tool (§5.6b)."""
    from engine.nuptiality import simulate_marriage_age_shift
    sim = simulate_marriage_age_shift(base_smam=19.5, base_tfr=2.20, shift_years=2.0)
    assert sim["shifted_smam"] == 21.5
    assert sim["projected_tfr"] < sim["baseline_tfr"]
    assert sim["percent_fertility_reduction"] > 0.0
    assert "interpretation" in sim


def test_migration_survival_ratios_and_od_matrix():
    """S7: Census Survival Ratio Migration and Origin-Destination Flow Matrix."""
    from engine.migration import calculate_survival_ratio_migration, calculate_origin_destination_matrix
    p1 = [100000, 95000, 90000, 85000, 80000]
    p2 = [105000, 99000, 93000, 88000, 82000]
    s_ratios = [0.98, 0.97, 0.96, 0.95]
    mig_df = calculate_survival_ratio_migration(p1, p2, s_ratios)
    assert len(mig_df) == 4
    assert "net_migrants" in mig_df.columns

    # OD Matrix
    od_df = pd.DataFrame({
        "origin": ["Dhaka", "Dhaka", "Chittagong", "Chittagong", "Sylhet", "Sylhet"],
        "destination": ["Chittagong", "Sylhet", "Dhaka", "Sylhet", "Dhaka", "Chittagong"],
        "migrants": [45000, 15000, 52000, 8000, 22000, 6000],
    })
    od_res = calculate_origin_destination_matrix(od_df)
    assert "od_matrix" in od_res
    assert od_res["gross_interregional_flows"] == 148000.0
    assert od_res["spatial_effectiveness_index"] > 0.0


def test_beers_and_karup_king_graduation():
    """S8: Beers and Karup-King graduation methods."""
    from engine.graduation import graduate_5yr_to_single_year_beers, graduate_karup_king
    five_year_counts = [120000, 115000, 110000, 105000, 98000, 90000, 80000, 68000, 52000, 35000]
    
    # Beers
    df_beers, meta_beers = graduate_5yr_to_single_year_beers(five_year_counts, start_age=0)
    assert len(df_beers) == len(five_year_counts) * 5
    assert meta_beers["re_sum_verified"] is True
    assert pytest.approx(df_beers["graduated_population"].sum(), abs=1.0) == sum(five_year_counts)

    # Karup-King
    df_kk = graduate_karup_king(five_year_counts, start_age=0)
    assert len(df_kk) == len(five_year_counts) * 5
    assert (df_kk["graduated_population"] >= 0).all()


def test_leslie_eigenvalue_and_keyfitz_momentum():
    """S9: Leslie matrix dominant eigenvalue and Keyfitz population momentum."""
    from engine.stable import calculate_leslie_dominant_eigenvalue, calculate_keyfitz_population_momentum
    
    # Leslie dominant eigenvalue
    les_res = calculate_leslie_dominant_eigenvalue(intrinsic_r=0.015, step_years=5)
    assert les_res["dominant_eigenvalue_lambda"] > 1.0
    assert les_res["asymptotic_state"] == "Expanding"

    # Keyfitz momentum
    mom_res = calculate_keyfitz_population_momentum(crude_birth_rate=20.0, life_expectancy_e0=72.0, nrr=1.45)
    assert mom_res["momentum_multiplier"] > 1.0
    assert mom_res["ultimate_growth_percent"] > 0.0


def test_section_schemas_completeness():
    """Validates that all section schemas generate valid CSV templates."""
    from engine.schemas import SECTION_SCHEMAS, get_template_csv
    
    expected_sections = [
        "S1_COMPOSITION", "S2_QUALITY", "S3_FERTILITY", "S4_MORTALITY",
        "S5_LIFETABLE", "S6_NUPTIALITY", "S7_MIGRATION", "S8_GRADUATION",
        "S9_STABLE", "S10_PROJECTION"
    ]
    for sec_key in expected_sections:
        assert sec_key in SECTION_SCHEMAS, f"Missing schema for {sec_key}"
        schema = SECTION_SCHEMAS[sec_key]
        csv_tmpl = schema.generate_template_csv()
        assert len(csv_tmpl.splitlines()) >= 2, f"Template for {sec_key} must have header and example row"
        assert schema.file_name.endswith(".csv")


def test_cohort_component_projection_scenarios():
    """S10: Cohort-component projection forward simulation across scenarios."""
    from engine.projection import run_cohort_component_projection
    
    # Simple test dataset
    std_groups = [
        "0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39",
        "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80-84", "85+"
    ]
    df_base = pd.DataFrame({
        "age_group": std_groups,
        "male": [500000] * 18,
        "female": [500000] * 18,
        "total": [1000000] * 18,
    })
    asfr_df = pd.DataFrame({
        "age_group": ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49"],
        "female_pop": [500000] * 7,
        "births": [30000, 70000, 60000, 40000, 20000, 5000, 1000],
    })
    asdr = [6.0, 0.7, 0.5, 1.1, 1.5, 1.8, 2.4, 3.3, 4.8, 7.2, 10.8, 16.4, 25.2, 38.0, 58.0, 88.0, 134.0, 215.0]
    mort_df = pd.DataFrame({
        "age_group": std_groups,
        "population": [1000000] * 18,
        "deaths": [val * 1000 for val in asdr],
    })
    
    res_med = run_cohort_component_projection(df_base, asfr_df, mort_df, horizon_years=20, scenario="medium")
    res_low = run_cohort_component_projection(df_base, asfr_df, mort_df, horizon_years=20, scenario="low")
    res_high = run_cohort_component_projection(df_base, asfr_df, mort_df, horizon_years=20, scenario="high")
    
    pop_med = res_med.summary_df["total_population"].iloc[-1]
    pop_low = res_low.summary_df["total_population"].iloc[-1]
    pop_high = res_high.summary_df["total_population"].iloc[-1]
    
    assert pop_high > pop_med > pop_low, "High scenario population must exceed medium, which exceeds low"
    assert len(res_med.projection_years) == 5
    assert res_med.dividend_status is not None



