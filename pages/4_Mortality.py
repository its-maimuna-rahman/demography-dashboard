"""Section 4: Mortality and standardization."""
import streamlit as st

from engine.schemas import SECTION_SCHEMAS
from engine.mortality import compute_block_d
from ui.theme import setup_page, page_header, label, notice, measure_grid, interpretations, show_plot, section_export
from ui.data_sources import sidebar_dataset
from ui.calculators import calculator_panel, multi_year_cdr_panel
from ui.components import create_mortality_schedule_chart

setup_page("Mortality", ":material/monitor_heart:")
page_header("Mortality & Standardization", "Death rates, infant and child survival, direct and indirect standardization")

ds, src = sidebar_dataset("s4", SECTION_SCHEMAS["S4_MORTALITY"], {
    "BBS SVRS 2022 (mortality schedule)": ("bbs_svrs_2022_mortality.csv", "BBS SVRS 2022 Mortality"),
    "National Census 2022 (benchmark)": ("census_2022.json", "National Census 2022"),
    "National Census 2011 (benchmark)": ("census_2011.json", "National Census 2011"),
})
notice(src, f"Dataset: {ds.name}")

measures = list(compute_block_d(ds).values())

label("Age pattern of mortality", 1)
with st.container(border=True):
    if ds.mortality_schedule is not None and not ds.mortality_schedule.empty:
        log_scale = st.toggle("Logarithmic scale", value=False, key="s4_log")
        show_plot(create_mortality_schedule_chart(ds.mortality_schedule, log_scale=log_scale), key="s4_asdr")
    else:
        st.info("This dataset has no age-specific mortality schedule.")

label("Measures", 2)
measure_grid(measures)
label("More mortality measures", 3)
extra = []
t_avg, t_calc = st.tabs(["Multi-year crude death rate", "Cause, infant, perinatal and maternal rates"])
with t_avg:
    extra += multi_year_cdr_panel("s4")
with t_calc:
    extra += calculator_panel("mortality", ds, prefix="s4")

label("Reading the results", 4)
interpretations("Plain-language interpretation", measures + extra)
section_export("Section 4: Mortality & Standardization", measures + extra, ds.name, ds.year, "S4_Mortality")
