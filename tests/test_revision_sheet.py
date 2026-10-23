"""Tests for the LaTeX formulas, interpretation style and revision-sheet measures."""
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from engine import extra_measures as xm
from engine.formulas import LATEX, formula_img_html, render_formula_svg
from engine.loader import load_demographic_dataset
from engine.registry import MEASURES_CATALOGUE
from engine.sex_composition import calculate_masculinity_proportion
from engine.stable import solve_lotka_intrinsic_r, compute_stable_population_measures

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "sample_data"


# ---------------------------------------------------------------- LaTeX
def test_every_measure_has_a_latex_formula():
    assert [c for c in MEASURES_CATALOGUE if c not in LATEX] == []


@pytest.mark.parametrize("code", sorted(LATEX))
def test_every_latex_formula_renders(code):
    svg = render_formula_svg(LATEX[code])
    assert svg.lstrip().startswith("<?xml") or "<svg" in svg


def test_formula_html_is_an_image_and_never_breaks():
    assert "data:image/svg+xml;base64," in formula_img_html(LATEX["TFR"], "TFR plain")
    broken = formula_img_html(r"\notarealcommand{x", "plain text formula")
    assert "plain text formula" in broken and "<img" not in broken


def test_latex_is_attached_to_results():
    m = calculate_masculinity_proportion(5000, 5000)
    assert m.formula_latex == LATEX["MP"]


# ---------------------------------------------------------------- interpretation style
def test_interpretation_line_matches_requested_style():
    m = calculate_masculinity_proportion(4958, 5042)
    assert m.interpretation_line == "MP = 49.58 : Roughly 49.58% of the population is male. The remaining 50.42% is female."


def test_every_catalogue_interpretation_is_short_and_formatted():
    for code, meta in MEASURES_CATALOGUE.items():
        text = meta["interp_func"](12.5, {"percent_excess": 1.0, "pct_0_14": 20.0, "pct_65_plus": 6.0, "sex": "female"})
        assert text and text.count(". ") <= 3 and len(text) < 330, (code, text)


# ---------------------------------------------------------------- measures from the revision sheet
def test_multi_year_cdr_matches_the_worked_example():
    r = xm.multi_year_cdr([10176, 10063, 9726], [1126000, 1171000, 1225000])
    assert r["CDR_AVG_V1"] == pytest.approx(8.523, abs=0.001)
    assert r["CDR_AVG_V2"] == pytest.approx(8.508, abs=0.001)
    assert r["CDR_AVG_V3"] == pytest.approx(8.5297, abs=0.0002)


def test_multi_year_cdr_even_years_use_mean_of_middle_two():
    r = xm.multi_year_cdr([100, 100, 100, 100], [1000, 1000, 2000, 2000])
    assert r["CDR_AVG_V3"] == pytest.approx(100 / 1500 * 1000)


def test_reed_merrell_coefficients_sum_to_interval_width():
    for code, width in {"RM_L0": 1, "RM_4L1": 4, "RM_L1": 1, "RM_3L2": 3, "RM_5L5": 5}.items():
        spec = next(s for s in xm.CALCULATORS["lifetable"] if s.code == code)
        probe = {i.key: 1.0 for i in spec.inputs}
        assert spec.compute(probe) == pytest.approx(width, abs=1e-9), code


def test_calculators_return_nothing_until_inputs_are_valid():
    spec = next(s for s in xm.CALCULATORS["mortality"] if s.code == "FD_RATE")
    assert xm.evaluate(spec, {"df": 5.0, "b": 0.0}) is None
    assert xm.evaluate(spec, {"df": 5.0, "b": 95.0}).raw_value == pytest.approx(50.0)


def test_adjusted_imr_formulas_and_separation_factor():
    a = next(s for s in xm.CALCULATORS["mortality"] if s.code == "AIMR_A")
    c = next(s for s in xm.CALCULATORS["mortality"] if s.code == "AIMR_C")
    assert xm.evaluate(a, {"d1": 30, "d2": 10, "b": 2000}).raw_value == pytest.approx(20.0)
    assert xm.evaluate(c, {"d1": 30, "d2": 10, "b1": 2000, "b0": 2000}).raw_value == pytest.approx(20.0)


def test_age_adjusted_birth_rate_equals_cbr_when_the_standard_is_the_study_population():
    women, births = np.array([100.0, 200.0, 150.0]), np.array([10.0, 30.0, 9.0])
    asfr = births / women
    assert xm.aabr_direct(asfr, women, 1000.0) == pytest.approx(births.sum() / 1000.0 * 1000.0)
    assert xm.aabr_indirect(births.sum(), 49.0, asfr, women) == pytest.approx(49.0)


def test_dissimilarity_and_relative_difference_of_identical_distributions_are_zero():
    r = xm.percent_distribution([10, 20, 30, 40])
    assert xm.index_of_dissimilarity(r, r) == 0
    assert np.allclose(xm.index_of_relative_difference(r, r), 0)
    assert xm.index_of_dissimilarity(xm.percent_distribution([1, 0]), xm.percent_distribution([0, 1])) == pytest.approx(100.0)


def test_total_rate_scales_with_age_group_width():
    assert xm.total_rate([1, 2], [100, 100], 5) == pytest.approx(5 * xm.total_rate([1, 2], [100, 100], 1))


def test_percentage_change():
    assert xm.percentage_change(100, 112) == pytest.approx(12.0)
    assert xm.percentage_change(0, 5) is None


def test_median_age_at_marriage_is_below_smam_and_sane():
    from engine.nuptiality import compute_nuptiality_section
    res = compute_nuptiality_section(load_demographic_dataset(SAMPLES / "bbs_census_2022_marital_status.csv"))
    assert 15 < res["MEDIAN_AGE_MARRIAGE"].raw_value < res["SMAM_FEMALE"].raw_value


def test_quadratic_approximation_is_close_to_the_exact_lotka_root():
    fert = load_demographic_dataset(SAMPLES / "bbs_svrs_stable_population.csv").fertility_schedule
    mort = load_demographic_dataset(SAMPLES / "bbs_svrs_2022_mortality.csv").mortality_schedule
    res = compute_stable_population_measures(fert, mort)
    assert res["R_QUAD"].raw_value == pytest.approx(res["LOTKA_R"].raw_value, abs=0.1)  # both in % per year
    assert res["BETA"].raw_value < 0                                                   # = minus the variance
    assert res["ALPHA"].raw_value == pytest.approx(res["MU"].raw_value)


def test_migration_extras_match_notes_definitions():
    ex = xm.compute_migration_extras(in_m=412000, out_m=615000, pop=100_000_000)
    assert ex["GROSS_MIG"].raw_value == 1_027_000 and ex["NET_MIG"].raw_value == -203_000
    assert ex["MER_SIGNED"].raw_value < 0                       # in-migration smaller than out-migration
    assert ex["IMRG"].raw_value == pytest.approx(4.12)


def test_extras_flow_into_the_sections_and_pipeline():
    from engine.pipeline import run_demographic_pipeline
    res = run_demographic_pipeline(load_demographic_dataset(SAMPLES / "census_2022.json"))
    assert {"PCT_0_14", "PCT_15_64", "PCT_65P"} <= set(res.measures)
    assert res.total_measures_target >= len(res.measures) - 15


# ---------------------------------------------------------------- look and feel
def test_theme_css_targets_current_streamlit_tabs_and_uses_pill_shapes():
    from ui.theme import CSS
    assert '[role="tab"]' in CSS and "border-radius:999px !important" in CSS
    assert "1.4rem" in CSS                      # section headings are large
    assert "border:1.5px solid var(--vs-sage)" in CSS  # status pills carry a green border
    assert "\\2212" not in CSS and "\x12" not in CSS    # no mangled escape sequences


def test_cards_show_a_formula_image_in_a_pill_toggle():
    from ui.theme import measure_card_html
    html = measure_card_html(calculate_masculinity_proportion(4958, 5042))
    assert "<summary>Formula</summary>" in html and "data:image/svg+xml;base64," in html


def test_tab_divider_line_is_hidden():
    from ui.theme import CSS
    assert '[role="tablist"]::after' in CSS
