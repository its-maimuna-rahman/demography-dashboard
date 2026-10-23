"""Section 1: Population composition and growth."""
import streamlit as st

from engine.schemas import SECTION_SCHEMAS
from engine.sex_composition import compute_block_a
from engine.age_dependency import compute_block_b
from ui.theme import setup_page, page_header, label, notice, measure_grid, interpretations, show_plot, section_export
from ui.data_sources import sidebar_dataset
from ui.calculators import percentage_change_panel, age_distribution_comparison_panel
from ui.components import create_population_pyramid, create_age_composition_donut

setup_page("Composition & Growth", ":material/groups:")
page_header("Composition & Growth", "Sex ratio, age structure and dependency")

ds, src = sidebar_dataset("s1", SECTION_SCHEMAS["S1_COMPOSITION"], {
    "BBS Census 2022 (5-year age-sex)": ("bbs_census_2022_age_sex.csv", "BBS Census 2022"),
    "BBS Census 2011 (5-year age-sex)": ("bbs_census_2011_age_sex.csv", "BBS Census 2011"),
    "National Census 2022 (benchmark)": ("census_2022.json", "National Census 2022"),
    "National Census 2011 (benchmark)": ("census_2011.json", "National Census 2011"),
})
notice(src, f"Dataset: {ds.name}" + (f" ({ds.year})" if ds.year else ""))

measures = list(compute_block_a(ds).values()) + list(compute_block_b(ds).values())

label("Population structure", 1)
pyr = ds.age_group_5yr if ds.age_group_5yr is not None else ds.single_year_ages
c1, c2 = st.columns([1.25, 1])
with c1:
    with st.container(border=True):
        if pyr is not None and {"male", "female"} <= set(pyr.columns):
            show_plot(create_population_pyramid(pyr, title=f"Population pyramid: {ds.name}"), key="s1_pyr")
        else:
            st.info("This dataset has no male/female age table, so no pyramid can be drawn.")
with c2:
    with st.container(border=True):
        if ds.pop_0_14 and ds.pop_15_64 and ds.pop_65_plus:
            show_plot(create_age_composition_donut(ds.pop_0_14, ds.pop_15_64, ds.pop_65_plus), key="s1_donut")
        else:
            st.info("Broad age groups (0-14, 15-64, 65+) are not available.")

label("Measures", 2)
measure_grid(measures)
label("More measures", 3)
extra = []
t_pc, t_dist = st.tabs(["Percentage change", "Age distribution comparison"])
with t_pc:
    extra += percentage_change_panel(ds)
with t_dist:
    extra += age_distribution_comparison_panel(ds)

label("Reading the results", 4)
interpretations("Plain-language interpretation", measures + extra)
section_export("Section 1: Composition & Growth", measures, ds.name, ds.year, "S1_Composition")
