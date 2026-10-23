"""Section 2: Data quality and census evaluation."""
import streamlit as st

from engine.schemas import SECTION_SCHEMAS
from engine.quality import (calculate_whipples_index, calculate_myers_blended_index,
                            calculate_un_joint_score, calculate_pec_comparison)
from ui.theme import setup_page, page_header, label, notice, quality_grid, show_plot, interpretations
from ui.data_sources import sidebar_dataset, load_sample
from ui.components import create_digit_preference_chart

setup_page("Data Quality", ":material/fact_check:")
page_header("Data Quality", "Age heaping, age-sex accuracy and census coverage")

ds, src = sidebar_dataset("s2", SECTION_SCHEMAS["S2_QUALITY"], {
    "Historical census with heaping (test fixture)": ("dirty_census.json", "Historical Dirty Census"),
    "BBS Census 2022 (single-year ages)": ("bbs_census_2022_single_year.csv", "BBS Census 2022 Single-Year"),
    "BBS Census 2022 (5-year age-sex)": ("bbs_census_2022_age_sex.csv", "BBS Census 2022"),
    "National Census 2022 (benchmark)": ("census_2022.json", "National Census 2022"),
})
notice(src, f"Dataset: {ds.name}")

# ---- Age heaping and accuracy
single = ds.single_year_ages if ds.single_year_ages is not None and not ds.single_year_ages.empty else None
whipple = calculate_whipples_index(single) if single is not None else None
myers = calculate_myers_blended_index(single) if single is not None else None
un_joint = None
if ds.age_group_5yr is not None and {"male", "female"} <= set(ds.age_group_5yr.columns):
    try:
        un_joint = calculate_un_joint_score(ds.age_group_5yr)
    except Exception:
        un_joint = None

# ---- Census coverage: only real inputs, never invented
with st.sidebar:
    st.markdown("**Census coverage (PEC)**")
    options = []
    rate_in_ds = ds.pec_omission_rate if ds.pec_omission_rate is not None else (
        1 - ds.census_coverage_rate if ds.census_coverage_rate is not None else None)
    if rate_in_ds is not None and ds.total_population:
        options.append("Use the dataset's own coverage rate")
    options += ["Bundled BBS PEC 2022 totals", "Enter a net omission rate", "Enter dual-system counts", "Skip coverage"]
    mode = st.radio("Coverage source", options, label_visibility="collapsed", key="s2_pec_mode")

pec = None
census_default = float(ds.total_population or 0)
if mode == "Use the dataset's own coverage rate":
    pec = calculate_pec_comparison(census_count=float(ds.total_population), omission_rate=float(rate_in_ds))
elif mode == "Bundled BBS PEC 2022 totals":
    pds = load_sample("bbs_pec_2022_totals.csv", "BBS PEC 2022")
    kv = {str(k): float(v) for k, v in zip(pds.raw_df["indicator"], pds.raw_df["value"])}
    pec = calculate_pec_comparison(census_count=kv["census_count"], omission_rate=kv["omission_rate"])
elif mode == "Enter a net omission rate":
    c1, c2 = st.columns(2)
    cc = c1.number_input("Census count", min_value=0.0, value=census_default, step=100000.0, key="s2_cc")
    om = c2.number_input("Net omission rate (%)", min_value=0.0, max_value=50.0, value=2.5, step=0.1, key="s2_om")
    if cc > 0:
        pec = calculate_pec_comparison(census_count=cc, omission_rate=om / 100.0)
elif mode == "Enter dual-system counts":
    c1, c2, c3 = st.columns(3)
    cc = c1.number_input("Census count", min_value=0.0, value=census_default, step=100000.0, key="s2_dcc")
    pc = c2.number_input("Post-enumeration survey count", min_value=0.0, value=0.0, step=100000.0, key="s2_pc")
    mc = c3.number_input("Matched count", min_value=0.0, value=0.0, step=100000.0, key="s2_mc")
    if cc > 0 and pc > 0 and mc > 0:
        pec = calculate_pec_comparison(census_count=cc, pec_count=pc, matched_count=mc)

label("Quality indicators", 1)
quality_grid([
    ("Whipple's index (digits 0 and 5)", whipple, "Needs a single-year age table covering ages 23-62."),
    ("Myers' blended index (all digits)", myers, "Needs a single-year age table covering ages 10-69."),
    ("UN age-sex accuracy index", un_joint, "Needs a 5-year table with male and female columns."),
    ("Census net undercount (%)", pec, "Choose a coverage source in the sidebar."),
])

label("Terminal digit preference", 2)
with st.container(border=True):
    if single is not None:
        show_plot(create_digit_preference_chart(single), key="s2_digits")
        if myers and myers.details:
            st.caption(f"Most preferred digit: {myers.details.get('most_preferred_digit')}. "
                       f"Most avoided digit: {myers.details.get('most_avoided_digit')}.")
    else:
        st.info("Digit preference needs single-year ages. Pick a single-year dataset or upload one.")

label("Guidance", 3)
with st.container(border=True):
    for title, chk in [("Whipple", whipple), ("Myers", myers), ("UN age-sex index", un_joint), ("Coverage", pec)]:
        if chk is not None and chk.score is not None:
            st.markdown(f"**{title}:** {chk.recommendation}")
