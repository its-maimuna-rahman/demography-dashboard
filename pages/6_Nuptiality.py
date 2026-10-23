"""Section 6: Nuptiality and marital dynamics."""
import streamlit as st

from engine.schemas import SECTION_SCHEMAS
from engine.nuptiality import compute_nuptiality_section, simulate_marriage_age_shift
from engine.projection import schedule_tfr
from ui.theme import setup_page, page_header, label, notice, measure_grid, interpretations, section_export, kpi_row
from ui.calculators import calculator_panel, total_marriage_rate_panel
from ui.data_sources import sidebar_dataset, read_sample_csv

setup_page("Nuptiality", ":material/favorite:")
page_header("Nuptiality", "Age at marriage, spousal age gap and marriage dynamics")

ds, src = sidebar_dataset("s6", SECTION_SCHEMAS["S6_NUPTIALITY"], {
    "BBS Census 2022 (marital status)": ("bbs_census_2022_marital_status.csv", "BBS Census 2022 Marital"),
    "National Census 2022 (benchmark)": ("census_2022.json", "National Census 2022"),
    "National Census 2011 (benchmark)": ("census_2011.json", "National Census 2011"),
})
notice(src, f"Dataset: {ds.name}")

measures_map = compute_nuptiality_section(ds)
measures = list(measures_map.values())

label("Indicators", 1)
if ds.marital_status_df is None:
    notice("No marital-status table in this dataset",
           "SMAM and the spousal age gap need counts by age group, sex and marital status. Marriage and divorce rates are shown when totals are present.", "amber")
measure_grid(measures)

label("More nuptiality measures", 2)
extra = []
t_rates, t_total = st.tabs(["Marriage and divorce rates", "Total marriage rates"])
with t_rates:
    extra += calculator_panel("nuptiality", ds, prefix="s6")
with t_total:
    extra += total_marriage_rate_panel(ds)

label("Delayed-marriage simulation", 3)
with st.container(border=True):
    st.caption("Bongaarts framework: later marriage shortens the years exposed to childbearing and lowers the TFR.")
    if "SMAM_FEMALE" in measures_map:
        smam = measures_map["SMAM_FEMALE"].raw_value
        st.markdown(f"Baseline female SMAM from this dataset: **{smam:.1f} years**.")
    else:
        smam = st.number_input("Baseline female SMAM (years)", 15.5, 40.0, 19.3, 0.1, help="No marital-status table loaded, so enter a value.")
    default_tfr = round(schedule_tfr(read_sample_csv("bbs_svrs_2022_fertility.csv")), 2)
    c1, c2 = st.columns(2)
    base_tfr = c1.number_input("Baseline TFR", 0.5, 8.0, default_tfr, 0.05, help=f"Default is the TFR of the bundled SVRS 2022 schedule ({default_tfr}).")
    shift = c2.slider("Marriage postponement (years)", 0.5, 5.0, 2.0, 0.5)
    try:
        sim = simulate_marriage_age_shift(base_smam=smam, base_tfr=base_tfr, shift_years=shift)
        kpi_row([("Baseline TFR", f"{sim['baseline_tfr']:.2f}", "children per woman"), ("Projected TFR", f"{sim['projected_tfr']:.2f}", f"after postponing marriage by {shift:g} years"),
                 ("Change in fertility", f"{-sim['percent_fertility_reduction']:.1f}%", "relative to baseline")])
        st.caption(sim["interpretation"])
    except ValueError as exc:
        st.warning(str(exc))

label("Reading the results", 4)
interpretations("Plain-language interpretation", measures + extra)
section_export("Section 6: Nuptiality", measures + extra, ds.name, ds.year, "S6_Nuptiality")
