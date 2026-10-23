"""Regression tests for bugs found during the debugging pass."""
import glob
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from engine.base import DemographicMeasureResult
from engine.graduation import (SPRAGUE_MIDDLE_PANEL, graduate_5yr_to_single_year_sprague, graduate_5yr_to_single_year_beers,
                               graduate_karup_king_with_diagnostics, carrier_farrag_smoothing)
from engine.inference import simulate_demographic_trajectory
from engine.loader import load_demographic_dataset
from engine.pipeline import run_demographic_pipeline

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "sample_data"
W = [x * 1e6 for x in [15.6, 16.1, 15.9, 14.8, 13.7, 12.5, 11.2, 9.9, 8.6, 7.2, 5.8, 4.4, 3.1, 2.0]]


def test_measure_result_does_not_require_citation():
    m = DemographicMeasureResult(code="X", name="X", block="b", raw_value=1.0, formatted_value="1", unit="u", formula="f")
    assert m.citation == ""


def test_sprague_multipliers_conserve_group_totals_without_rescaling():
    assert np.allclose(SPRAGUE_MIDDLE_PANEL.sum(axis=0), [0, 0, 1, 0, 0])
    assert np.allclose(SPRAGUE_MIDDLE_PANEL.sum(axis=1), 0.2)
    from engine.graduation import _sprague_raw
    raw = _sprague_raw(W)
    for i, w in enumerate(W):
        assert raw[i * 5:(i + 1) * 5].sum() == pytest.approx(w, rel=1e-9)


@pytest.mark.parametrize("fn", [graduate_5yr_to_single_year_sprague, graduate_5yr_to_single_year_beers,
                                lambda w, s=0, **k: graduate_karup_king_with_diagnostics(w, s, **k)])
def test_graduation_methods_conserve_every_group(fn):
    df, diag = fn(W, 0)
    assert len(df) == 70 and (df["graduated_population"] >= 0).all()
    assert diag["max_group_re_sum_difference"] < 1e-6


def test_open_ended_group_is_not_split():
    df, diag = graduate_5yr_to_single_year_sprague(W + [1.5e6], 0, open_last_group=True)
    assert len(df) == 70 and diag["open_interval_total"] == 1.5e6


def test_smoothing_preserves_total():
    assert sum(carrier_farrag_smoothing(W)) == pytest.approx(sum(W))


@pytest.mark.parametrize("path", [p for p in sorted(glob.glob(str(SAMPLES / "*"))) if p.endswith((".csv", ".json")) and "time_series" not in p])
def test_every_bundled_dataset_loads_and_runs_pipeline(path):
    ds = load_demographic_dataset(Path(path))
    run_demographic_pipeline(ds)  # must not raise


def test_schedule_files_are_not_mistaken_for_population_tables():
    fert = load_demographic_dataset(SAMPLES / "bbs_svrs_2022_fertility.csv")
    assert fert.total_population is None and fert.fertility_schedule is not None
    mort = load_demographic_dataset(SAMPLES / "bbs_svrs_2022_mortality.csv")
    assert mort.mortality_schedule is not None and "male" not in mort.age_group_5yr.columns


def test_migration_totals_populate_flows():
    ds = load_demographic_dataset(SAMPLES / "bbs_svrs_2022_migration_totals.csv")
    assert ds.in_migrants and ds.out_migrants and ds.total_population and ds.previous_census_pop
    assert "NMRG" in run_demographic_pipeline(ds).measures


def test_gdvr_is_not_invented_from_married_women():
    ds = load_demographic_dataset(SAMPLES / "census_2022.json")
    assert "GDVR" not in run_demographic_pipeline(ds).measures  # no marital-status table, so unavailable


@pytest.mark.parametrize("scenario", ["low", "medium", "high"])
def test_module2_trajectory_schema_and_scenarios(scenario):
    ts = pd.read_csv(SAMPLES / "time_series_1970_2024.csv")
    res = simulate_demographic_trajectory(ts, 30, scenario)
    for col in ["tfr", "pct_working_15_64", "pct_elderly_65_plus", "oadr", "is_projected"]:
        assert col in res.combined_df.columns
    assert res.combined_df[["tfr", "pct_working_15_64", "pct_elderly_65_plus"]].notna().all().any()
    assert len(res.projected_df) == 30


def test_module2_scenarios_are_ordered():
    ts = pd.read_csv(SAMPLES / "time_series_1970_2024.csv")
    end = {s: simulate_demographic_trajectory(ts, 30, s).projected_df["total_population"].iloc[-1] for s in ["low", "medium", "high"]}
    assert end["low"] < end["medium"] < end["high"]


def test_module2_uses_supplied_tables():
    ts = pd.read_csv(SAMPLES / "time_series_1970_2024.csv")
    res = simulate_demographic_trajectory(
        ts, 20, "medium", base_age_sex_df=pd.read_csv(SAMPLES / "bbs_census_2022_age_sex.csv"),
        fertility_schedule=pd.read_csv(SAMPLES / "bbs_svrs_2022_fertility.csv"), mortality_schedule=pd.read_csv(SAMPLES / "bbs_svrs_2022_mortality.csv"))
    assert any("supplied age-sex table" in a for a in res.assumptions_summary)


def test_summary_brief_is_shorter_than_detailed_report():
    from reports.pdf_export import generate_detailed_pdf_report, generate_summary_pdf_brief
    res = run_demographic_pipeline(load_demographic_dataset(SAMPLES / "census_2022.json"))
    assert len(generate_summary_pdf_brief(res)) < len(generate_detailed_pdf_report(res))


def test_no_emoji_in_source_file_names():
    for p in ROOT.rglob("*.py"):
        assert all(ord(ch) < 0x2000 or ch in "–—" for ch in p.name), f"emoji in file name: {p.name}"
