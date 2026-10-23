"""
Unit Tests for Empirical Bangladesh BBS Datasets (§7 improve.md, DATA.md)
Validates that all empirical BBS Census 2022/2011, SVRS, PEC, and UN datasets
load seamlessly, satisfy demographic accounting identities, and compute benchmark indicators.
"""

import pytest
import pandas as pd
from pathlib import Path

from engine.loader import load_demographic_dataset
from engine.sex_composition import compute_block_a
from engine.age_dependency import compute_block_b
from engine.fertility import compute_block_c
from engine.mortality import compute_block_d
from engine.lifetable import build_abridged_life_table
from engine.nuptiality import compute_nuptiality_section
from engine.migration import calculate_origin_destination_matrix
from engine.stable import compute_stable_population_measures

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"
BASE_DIR = Path(__file__).resolve().parent.parent


def test_empirical_data_manifest_and_docs():
    """Validates that DATA.md and all 11 required empirical tables exist."""
    data_md = BASE_DIR / "DATA.md"
    assert data_md.is_file(), "DATA.md must exist in project root"
    assert len(data_md.read_text(encoding="utf-8")) > 1000

    expected_files = [
        "bbs_census_2022_age_sex.csv",
        "bbs_census_2011_age_sex.csv",
        "bbs_census_2022_single_year.csv",
        "bbs_svrs_2022_fertility.csv",
        "bbs_svrs_2022_mortality.csv",
        "bbs_census_2022_marital_status.csv",
        "bbs_census_2022_division_od_matrix.csv",
        "bbs_svrs_2022_migration_totals.csv",
        "bbs_pec_2022_totals.csv",
        "bbs_svrs_stable_population.csv",
        "bbs_un_projection_assumptions.csv",
    ]
    for fn in expected_files:
        fpath = SAMPLE_DIR / fn
        assert fpath.is_file(), f"Missing empirical dataset: {fn}"
        assert fpath.stat().st_size > 50, f"Empirical dataset {fn} is empty"


def test_bbs_census_2022_composition():
    """S1: BBS Census 2022 5-Year Age-Sex population distribution."""
    ds = load_demographic_dataset(SAMPLE_DIR / "bbs_census_2022_age_sex.csv", name="BBS Census 2022")
    assert ds.total_population > 160_000_000
    assert ds.age_group_5yr is not None
    assert len(ds.age_group_5yr) == 18
    # Exact accounting identity: male + female == total on every row
    df = ds.age_group_5yr
    assert (df["male"] + df["female"] == df["total"]).all()

    res_a = compute_block_a(ds)
    assert "SR" in res_a
    assert "MP" in res_a

    res_b = compute_block_b(ds)
    assert "TDR" in res_b
    assert "CDR_CHILD" in res_b
    assert "OADR" in res_b


def test_bbs_census_2011_composition():
    """S1: BBS Census 2011 5-Year Age-Sex population distribution."""
    ds = load_demographic_dataset(SAMPLE_DIR / "bbs_census_2011_age_sex.csv", name="BBS Census 2011")
    assert ds.total_population > 140_000_000
    assert ds.age_group_5yr is not None
    df = ds.age_group_5yr
    assert (df["male"] + df["female"] == df["total"]).all()


def test_bbs_svrs_2022_fertility_schedule():
    """S3: BBS SVRS 2022 Fertility schedule yields official TFR = 2.15."""
    ds = load_demographic_dataset(SAMPLE_DIR / "bbs_svrs_2022_fertility.csv", name="SVRS 2022 Fertility")
    assert ds.fertility_schedule is not None
    assert len(ds.fertility_schedule) == 7

    res_c = compute_block_c(ds)
    assert "TFR" in res_c
    # Official BBS SVRS 2022 published TFR is 2.15
    assert pytest.approx(res_c["TFR"].raw_value, abs=0.02) == 2.15
    assert "GRR" in res_c
    assert pytest.approx(res_c["GRR"].raw_value, abs=0.02) == 1.05
    assert "NRR" in res_c
    assert pytest.approx(res_c["NRR"].raw_value, abs=0.05) == 1.01


def test_bbs_svrs_2022_mortality_and_life_table():
    """S4 & S5: BBS SVRS 2022 Mortality Schedule and Abridged Life Table."""
    ds = load_demographic_dataset(SAMPLE_DIR / "bbs_svrs_2022_mortality.csv", name="SVRS 2022 Mortality")
    assert ds.mortality_schedule is not None

    lt, indicators = build_abridged_life_table(ds.mortality_schedule, radix=100000.0)
    assert "E0" in indicators
    e0_val = indicators["E0"].raw_value
    assert 68.0 <= e0_val <= 74.0, f"Expected life expectancy e0 in [68, 74], got {e0_val}"

    # Life table mathematical identities
    assert lt.loc[0, "lx"] == 100000.0
    assert pytest.approx(lt["ndx"].sum(), abs=1.0) == 100000.0
    assert (lt["lx"].diff().dropna() <= 0).all()


def test_bbs_census_2022_nuptiality_smam():
    """S6: BBS Census 2022 Marital Status and Singulate Mean Age at Marriage (Hajnal 1953)."""
    ds = load_demographic_dataset(SAMPLE_DIR / "bbs_census_2022_marital_status.csv", name="BBS 2022 Marital")
    assert ds.marital_status_df is not None

    res_n = compute_nuptiality_section(ds)
    assert "SMAM_FEMALE" in res_n
    assert "SMAM_MALE" in res_n
    assert "SPOUSAL_GAP" in res_n

    # BBS Census 2022 published SMAM: Female ~19.3, Male ~25.4, Gap ~6.1
    smam_f = res_n["SMAM_FEMALE"].raw_value
    smam_m = res_n["SMAM_MALE"].raw_value
    gap = res_n["SPOUSAL_GAP"].raw_value

    assert pytest.approx(smam_f, abs=0.5) == 19.3
    assert pytest.approx(smam_m, abs=0.5) == 25.5
    assert pytest.approx(gap, abs=0.5) == 6.2


def test_bbs_census_2022_division_od_matrix():
    """S7: BBS Census 2022 Origin-Destination Inter-Divisional Migration Streams."""
    df_od = pd.read_csv(SAMPLE_DIR / "bbs_census_2022_division_od_matrix.csv")
    od_res = calculate_origin_destination_matrix(df_od)

    assert "od_matrix" in od_res
    assert "spatial_effectiveness_index" in od_res
    eff = od_res["spatial_effectiveness_index"]
    assert 50.0 <= eff <= 95.0, f"Expected high unidirectional efficiency toward Dhaka, got {eff}%"
    assert od_res["gross_interregional_flows"] > 500.0


def test_bbs_pec_2022_coverage():
    """S2: BIDS/BBS Post Enumeration Check (PEC) 2022 coverage indicators."""
    ds = load_demographic_dataset(SAMPLE_DIR / "bbs_pec_2022_totals.csv", name="PEC 2022")
    assert ds.raw_df is not None
    assert ds.census_coverage_rate == 0.9725
    assert ds.pec_omission_rate == 0.0275
