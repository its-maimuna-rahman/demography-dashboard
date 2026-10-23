"""
Overview page of the Vital Stats Suite (loaded by app.py).

Run the suite with:  streamlit run app.py
Module 1 audits one dataset (or compares two) across the full measure battery.
Module 2 projects a historical series forward and flags policy-relevant thresholds.
The ten section pages are listed in the sidebar.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent

from engine.base import DemographicDataset
from engine.pipeline import run_demographic_pipeline, compare_two_datasets
from engine.quality import validate_dataset_completeness
from engine.missing_assistant import explain_missing_gap
from engine.inference import simulate_demographic_trajectory
from engine.loader import load_demographic_dataset, generate_sample_age_distribution_csv, generate_sample_summary_csv
from engine.schemas import get_template_csv
from engine.lifetable import build_abridged_life_table
from engine.graduation import graduate_5yr_to_single_year_sprague
from reports.pdf_export import generate_detailed_pdf_report, generate_summary_pdf_brief
from reports.html_export import generate_standalone_html_dashboard
from ui.theme import (setup_page, page_header, label, notice, kpi_row, measure_grid, quality_grid, interpretations,
                      show_plot, show_df, pill, tone_for)
from ui.data_sources import default_projection_inputs, read_sample_csv
from ui.components import (create_population_pyramid, create_age_composition_donut, create_digit_preference_chart,
                           create_fertility_schedule_chart, create_mortality_schedule_chart, create_life_table_curves,
                           create_sprague_graduation_chart, create_trajectory_chart, render_calm_gauge)

setup_page("Overview", ":material/home:")

SAMPLES = BASE_DIR / "sample_data"
BENCHMARKS = {
    "National Census 2022 (modern transition)": ("census_2022.json", "National Census 2022"),
    "National Census 2011 (baseline)": ("census_2011.json", "National Census 2011"),
    "Historical census with heaping and gaps": ("dirty_census.json", "Historical Dirty Census"),
    "BBS Census 2022 (5-year age-sex)": ("bbs_census_2022_age_sex.csv", "BBS Census 2022"),
    "BBS Census 2011 (5-year age-sex)": ("bbs_census_2011_age_sex.csv", "BBS Census 2011"),
    "BBS SVRS 2022 (fertility schedule)": ("bbs_svrs_2022_fertility.csv", "BBS SVRS 2022 Fertility"),
    "BBS SVRS 2022 (mortality schedule)": ("bbs_svrs_2022_mortality.csv", "BBS SVRS 2022 Mortality"),
    "BBS Census 2022 (marital status)": ("bbs_census_2022_marital_status.csv", "BBS Census 2022 Marital Status"),
    "BBS SVRS 2022 (migration totals)": ("bbs_svrs_2022_migration_totals.csv", "BBS SVRS 2022 Migration"),
}


def load_benchmark(choice: str) -> DemographicDataset:
    fname, disp = BENCHMARKS[choice]
    path = SAMPLES / fname
    if not path.is_file():
        st.error(f"Bundled dataset '{fname}' is missing. Run `python sample_data/generate_samples.py`.")
        st.stop()
    return load_demographic_dataset(path, name=disp)


def load_upload(file, label_text: str) -> Optional[DemographicDataset]:
    try:
        return load_demographic_dataset(file, name=label_text)
    except Exception as exc:
        st.error(f"Could not read '{file.name}': {exc}. Check the columns against the templates in the sidebar.")
        st.stop()


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown("### Vital Stats Suite")
    st.caption("Choose a dataset, optionally compare it with a second one, and use the pages above for each syllabus section.")
    st.markdown("**Primary dataset**")
    src_type = st.radio("Source", ["Bundled", "Upload"], horizontal=True, label_visibility="collapsed", key="src_primary")
    primary: Optional[DemographicDataset] = None
    if src_type == "Bundled":
        choice = st.selectbox("Bundled dataset", list(BENCHMARKS), key="bench_primary")
        primary = load_benchmark(choice)
    else:
        up = st.file_uploader("CSV or JSON", type=["csv", "json"], key="up_primary",
                              help="An age-sex table (age or age_group, male, female, total, optional births and deaths), an indicators table (indicator, value) or a JSON dataset.")
        if up is not None:
            primary = load_upload(up, st.text_input("Label", value=up.name.rsplit(".", 1)[0], key="name_primary"))

    st.divider()
    compare_on = st.toggle("Compare with a second dataset", value=False, key="cmp_on")
    other: Optional[DemographicDataset] = None
    if compare_on:
        c_type = st.radio("Comparison source", ["Bundled", "Upload"], horizontal=True, label_visibility="collapsed", key="src_cmp")
        if c_type == "Bundled":
            names = list(BENCHMARKS)
            other = load_benchmark(st.selectbox("Comparison dataset", names, index=1, key="bench_cmp"))
        else:
            up2 = st.file_uploader("Second CSV or JSON", type=["csv", "json"], key="up_cmp")
            if up2 is not None:
                other = load_upload(up2, st.text_input("Label", value=up2.name.rsplit(".", 1)[0], key="name_cmp"))
            else:
                st.info("Upload a second file to compare.")

    st.divider()
    with st.expander("CSV templates"):
        st.download_button("Age-sex distribution", generate_sample_age_distribution_csv(), "population_age_sex.csv", "text/csv", key="t1")
        st.download_button("Key indicators", generate_sample_summary_csv(), "population_indicators.csv", "text/csv", key="t2")
        for lbl, key, fn in [("Fertility schedule", "S3_FERTILITY", "fertility_age.csv"), ("Mortality schedule", "S4_MORTALITY", "mortality_age_sex.csv"),
                             ("Marital status", "S6_NUPTIALITY", "marital_status.csv"), ("Migration totals", "S7_MIGRATION", "migration_totals.csv"),
                             ("Projection assumptions", "S11_PROJECTION", "projection_assumptions.csv")]:
            st.download_button(lbl, get_template_csv(key), fn, "text/csv", key=f"tpl_{key}")
    with st.expander("Assistant settings"):
        gemini_key = st.text_input("Gemini API key (optional)", type="password", help="Used only to word the explanations of missing data. Without it, built-in text is used.")

if primary is None:
    page_header("Vital Stats Suite", "Demographic diagnostics and policy projection")
    notice("Choose a dataset to begin", "Pick a bundled dataset or upload your own file in the sidebar.")
    st.stop()

page_header("Vital Stats Suite", "Demographic diagnostics and policy projection")
tab1, tab2, tab3 = st.tabs(["Module 1: Diagnostics", "Module 2: Projection and policy", "Reference"])

# ================================================================== MODULE 1
with tab1:
    result = run_demographic_pipeline(primary)
    st.markdown(f"## {primary.name}")
    kpi_row([
        ("Total population", f"{primary.total_population:,.0f}" if primary.total_population else "Not available"),
        ("Year", f"{primary.year}" if primary.year else "Not stated"),
        ("Scope", primary.region or "National"),
        ("Measures computed", f"{result.computable_count} of {result.total_measures_target}"),
    ])
    if compare_on and other is not None:
        st.caption(f"Comparing with: {other.name}")

    label("Summary", 1)
    with st.container(border=True):
        st.markdown(result.executive_summary)

    if result.top_concerns:
        label("Priority concerns", 2)
        cards = []
        import html as _h
        for c in result.top_concerns[:4]:
            sev = str(c.get("severity", "WARNING"))
            cards.append(f'<div class="vs-mcard" style="min-height:150px"><div class="vs-mfoot">{pill(sev.title(), tone_for(sev))}</div>'
                         f'<div class="vs-mname">{_h.escape(str(c.get("title", "")))}</div>'
                         f'<div class="vs-munit">{_h.escape(str(c.get("description", "")))}</div>'
                         f'<div class="vs-munit">{_h.escape(str(c.get("recommendation", "")))}</div></div>')
        st.html(f'<div class="vs-grid">{"".join(cards)}</div>')

    _, missing_codes, gaps = validate_dataset_completeness(primary)
    if missing_codes:
        with st.expander(f"{len(missing_codes)} measures need more data"):
            st.caption("These fields were not found in the dataset. Each note explains how to supply them.")
            for gap_key in gaps:
                info = explain_missing_gap(gap_key, api_key=gemini_key or None)
                with st.container(border=True):
                    st.markdown(f"**{info['title']}**")
                    st.write(info["explanation"])

    label("Data quality", 3)
    quality_grid([
        ("Whipple's index", result.quality_checks.get("WHIPPLE"), "Needs a single-year age table (ages 23-62)."),
        ("Myers' blended index", result.quality_checks.get("MYERS"), "Needs a single-year age table (ages 10-69)."),
        ("UN age-sex accuracy index", result.quality_checks.get("UN_JOINT_SCORE"), "Needs a 5-year table with male and female columns."),
        ("Census net undercount (%)", result.quality_checks.get("PEC"), "No coverage rate in this dataset. Use the Data Quality page to enter one."),
    ])

    label("Visualizations", 4)
    vt = st.tabs(["Pyramid", "Age composition", "Digit preference", "Fertility and mortality", "Life table", "Graduation"])
    pyr_df = primary.age_group_5yr if primary.age_group_5yr is not None else primary.single_year_ages
    has_sex = pyr_df is not None and {"male", "female"} <= set(pyr_df.columns)
    with vt[0]:
        if has_sex:
            mode = st.radio("Show", ["Percentage", "Counts"], horizontal=True, key="pyr_mode")
            cmp_df = None
            if compare_on and other is not None:
                cmp_df = other.age_group_5yr if other.age_group_5yr is not None else other.single_year_ages
                if cmp_df is not None and not {"male", "female"} <= set(cmp_df.columns):
                    cmp_df = None
            show_plot(create_population_pyramid(pyr_df, title=f"Population pyramid: {primary.name}", df_compare=cmp_df,
                                                current_label=str(primary.year or primary.name),
                                                compare_label=str(other.year or other.name) if (other and cmp_df is not None) else None,
                                                as_percentage=(mode == "Percentage")), key="home_pyr")
        else:
            st.info("This dataset has no male/female age table.")
    with vt[1]:
        if primary.pop_0_14 and primary.pop_15_64 and primary.pop_65_plus:
            show_plot(create_age_composition_donut(primary.pop_0_14, primary.pop_15_64, primary.pop_65_plus), key="home_donut")
        else:
            st.info("Broad age groups (0-14, 15-64, 65+) are not available.")
    with vt[2]:
        if primary.single_year_ages is not None and not primary.single_year_ages.empty:
            show_plot(create_digit_preference_chart(primary.single_year_ages), key="home_digits")
        else:
            st.info("Digit preference needs a single-year age table.")
    with vt[3]:
        a, b = st.columns(2)
        with a:
            if primary.fertility_schedule is not None and not primary.fertility_schedule.empty:
                show_plot(create_fertility_schedule_chart(primary.fertility_schedule), key="home_asfr")
            else:
                st.info("No fertility schedule in this dataset.")
        with b:
            if primary.mortality_schedule is not None and not primary.mortality_schedule.empty:
                show_plot(create_mortality_schedule_chart(primary.mortality_schedule, log_scale=st.toggle("Log scale", key="home_log")), key="home_asdr")
            else:
                st.info("No mortality schedule in this dataset.")
    with vt[4]:
        if primary.mortality_schedule is not None and not primary.mortality_schedule.empty:
            try:
                lt_df, _ = build_abridged_life_table(primary.mortality_schedule)
                show_plot(create_life_table_curves(lt_df, title=f"Survivorship: {primary.name}"), key="home_lt")
            except Exception as exc:
                st.warning(f"Could not build a life table: {exc}")
        else:
            st.info("A mortality schedule is needed for a life table.")
    with vt[5]:
        t5 = primary.age_group_5yr
        if t5 is not None and len(t5) >= 6 and ("total" in t5.columns):
            labels5 = t5["age_group"].astype(str).tolist()
            open_last = labels5[-1].endswith("+")
            counts = t5["total"].astype(float).tolist()
            closed = counts[:-1] if open_last else counts
            try:
                g, meta = graduate_5yr_to_single_year_sprague(counts, 0, open_last_group=open_last)
                show_plot(create_sprague_graduation_chart(closed, g, 0), key="home_grad")
                st.caption(f"Largest group difference after graduation: {meta['max_group_re_sum_difference']:.4f} persons.")
            except Exception as exc:
                st.warning(f"Graduation could not run: {exc}")
        else:
            st.info("Graduation needs at least six 5-year age groups.")

    if compare_on and other is not None:
        label("Comparison")
        comp = compare_two_datasets(primary, other)
        with st.container(border=True):
            st.markdown(comp.narrative_summary)
        show_df(comp.comparison_table, hide_index=True)

    label("Measures by block", 5)
    BLOCKS = [
        ("Sex composition", ["MP", "SR", "SRB", "EXCESS_M"]),
        ("Age structure", ["ACR", "TDR", "CDR_CHILD", "OADR", "AI", "PSR", "MEDIAN_AGE", "CWR", "DENSITY", "GROWTH_RATE", "PCT_0_14", "PCT_15_64", "PCT_65P"]),
        ("Fertility", ["CBR", "MBR", "GFR", "ASFR", "TFR", "GRR", "NRR", "MAC", "PROP_FEMALE_BIRTHS", "GRR_SHORT"]),
        ("Mortality", ["CDR", "CORRECTED_CDR", "NMR", "ENMR", "PNMR", "IMR", "CMR", "U5MR", "MMR", "ASDR", "DSDR", "SMR", "ISDR"]),
        ("Nuptiality", ["SMAM_FEMALE", "SMAM_MALE", "SPOUSAL_GAP", "CELIBACY", "CMRG", "CDVR", "GDVR", "GMR", "MEDIAN_AGE_MARRIAGE"]),
        ("Migration", ["NMRG", "MER", "IMRG", "OMRG", "GROSS_MIG", "NET_MIG", "MER_SIGNED"]),
        ("Stable population", ["LOTKA_R", "INTRINSIC_B", "INTRINSIC_D", "GEN_LEN", "R1", "R2", "MU", "ALPHA", "BETA", "R_QUAD", "T_QUAD"]),
    ]
    btabs = st.tabs([b[0] for b in BLOCKS])
    for tab, (bname, codes) in zip(btabs, BLOCKS):
        with tab:
            ms = [result.measures[c] for c in codes if c in result.measures]
            if not ms:
                st.info(f"No {bname.lower()} measures could be computed from this dataset.")
                continue
            measure_grid(ms)
            with st.expander("Benchmark gauges"):
                for m in ms:
                    i = m.interpretation or {}
                    render_calm_gauge(m.name, m.raw_value, m.formatted_value, m.unit, i.get("status", "MODERATE"), i.get("label", "Reference range"),
                                      i.get("gauge_min", 0.0), i.get("gauge_max", 100.0), i.get("source", "Demographic standard"), i.get("is_heuristic", False))
            interpretations(f"{bname}: plain-language interpretation", ms)

    label("Export", 6)
    sig = f"{primary.name}|{primary.year}|{primary.total_population}|{result.computable_count}|{hash(result.executive_summary)}"
    if st.session_state.get("export_sig") != sig:
        st.session_state["export_files"] = {
            "pdf": generate_detailed_pdf_report(result), "brief": generate_summary_pdf_brief(result),
            "html": generate_standalone_html_dashboard(result),
        }
        st.session_state["export_sig"] = sig
    files = st.session_state["export_files"]
    stub = primary.name.replace(" ", "_")
    e1, e2, e3 = st.columns(3)
    with e1:
        with st.container(border=True):
            st.markdown("**Detailed PDF**")
            st.caption("Every measure with values, status and interpretation.")
            st.download_button("Download PDF", files["pdf"], f"Demographic_Report_{stub}.pdf", "application/pdf", key="dl_pdf")
    with e2:
        with st.container(border=True):
            st.markdown("**Summary brief**")
            st.caption("Top concerns and key findings.")
            st.download_button("Download brief", files["brief"], f"Executive_Brief_{stub}.pdf", "application/pdf", key="dl_brief")
    with e3:
        with st.container(border=True):
            st.markdown("**Standalone HTML**")
            st.caption("Self-contained dashboard for offline sharing.")
            st.download_button("Download HTML", files["html"], f"Dashboard_{stub}.html", "text/html", key="dl_html")

# ================================================================== MODULE 2
with tab2:
    st.markdown("## Projection and policy")
    st.caption("Project a historical series forward with a cohort-component model and screen for policy thresholds.")
    hist_up = st.file_uploader("Historical series CSV (optional)", type=["csv"], key="hist_up",
                               help="Needs year and total_population. For best results add TFR, life_expectancy, pct_youth, pct_working_age and pct_elderly.")
    try:
        hist = pd.read_csv(hist_up) if hist_up is not None else read_sample_csv("time_series_1970_2024.csv")
    except Exception as exc:
        st.error(f"Could not read the series: {exc}")
        st.stop()
    with st.container(border=True):
        c1, c2 = st.columns(2)
        horizon = c1.slider("Horizon (years)", 10, 50, 30, 5, key="m2_h")
        scen = c2.radio("Fertility scenario", ["Medium", "Low", "High"], horizontal=True, key="m2_s").lower()
    try:
        tables = default_projection_inputs()
        a = read_sample_csv("bbs_un_projection_assumptions.csv")
        av = {str(k): float(v) for k, v in zip(a["indicator"], a["value"])}
        targets = {"low": av["tfr_low_variant"], "medium": av["tfr_med_variant"], "high": av["tfr_high_variant"]}
        proj = simulate_demographic_trajectory(
            hist, horizon, scen, base_age_sex_df=tables["age_sex"], fertility_schedule=tables["fertility"],
            mortality_schedule=tables["mortality"], srb=av.get("srb", 105.0), net_migration_annual=av.get("net_migration_annual", 0.0), tfr_targets=targets)
    except Exception as exc:
        st.error(f"The projection could not run: {exc}")
        st.stop()
    label("Outlook", 1)
    with st.container(border=True):
        st.markdown(proj.narrative_policy_brief)
        st.caption(f"Current phase: {proj.current_phase}")
    show_plot(create_trajectory_chart(proj.combined_df, proj.dividend_start_year, proj.dividend_end_year), key="m2_chart")
    with st.expander("Model assumptions"):
        for s in proj.assumptions_summary:
            st.markdown(f"- {s}")
    label("Policy flags", 2)
    for f in proj.policy_flags:
        with st.container(border=True):
            st.html(f'<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><b>{f.title}</b>{pill(f.severity.title(), tone_for(f.severity))}</div>')
            st.write(f.description)
            st.caption(f"Trigger: {f.rationale}")
            for rec in f.policy_recommendations:
                st.markdown(f"- {rec}")

# ================================================================== REFERENCE
with tab3:
    st.markdown("## Reference")
    st.caption("Methods follow UN DESA, WHO and standard demographic texts (Preston et al. 2001; Shryock & Siegel 1976; Bhende & Kanitkar 2010).")
    for fname in ["ENGINE.md", "docs/METHODS.md"]:
        p = BASE_DIR / fname
        if p.is_file():
            with st.expander(fname.split("/")[-1], expanded=(fname == "ENGINE.md")):
                st.markdown(p.read_text(encoding="utf-8"))
