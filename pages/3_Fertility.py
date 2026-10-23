"""Section 3: Fertility and reproduction."""
import streamlit as st

from engine.schemas import SECTION_SCHEMAS
from engine.fertility import compute_block_c, compute_bongaarts_determinants
from ui.theme import setup_page, page_header, label, notice, measure_grid, interpretations, show_plot, section_export
from ui.data_sources import sidebar_dataset
from ui.calculators import calculator_panel, aabr_panel
from ui.theme import kpi_row
from ui.components import create_fertility_schedule_chart

setup_page("Fertility", ":material/child_care:")
page_header("Fertility & Reproduction", "ASFR, TFR, reproduction rates and proximate determinants")

ds, src = sidebar_dataset("s3", SECTION_SCHEMAS["S3_FERTILITY"], {
    "BBS SVRS 2022 (fertility schedule)": ("bbs_svrs_2022_fertility.csv", "BBS SVRS 2022 Fertility"),
    "National Census 2022 (benchmark)": ("census_2022.json", "National Census 2022"),
    "National Census 2011 (benchmark)": ("census_2011.json", "National Census 2011"),
})
notice(src, f"Dataset: {ds.name}")

measures_map = compute_block_c(ds)
measures = list(measures_map.values())

label("Age pattern of fertility", 1)
with st.container(border=True):
    if ds.fertility_schedule is not None and not ds.fertility_schedule.empty:
        show_plot(create_fertility_schedule_chart(ds.fertility_schedule), key="s3_asfr")
    else:
        st.info("This dataset has no age-specific fertility schedule.")

label("Measures", 2)
measure_grid(measures)

label("More fertility measures", 3)
extra = []
t_rates, t_aabr = st.tabs(["Order of birth and marital duration", "Age-adjusted birth rates"])
with t_rates:
    extra += calculator_panel("fertility", ds, prefix="s3")
with t_aabr:
    extra += aabr_panel(ds)

label("Proximate determinants (Bongaarts)", 4)
tfr_obs = measures_map["TFR"].raw_value if "TFR" in measures_map else None
with st.container(border=True):
    st.caption("Adjust the four indices. The model multiplies them by total fecundity (15.3 births per woman).")
    c1, c2, c3, c4 = st.columns(4)
    cm = c1.slider("Marriage (Cm)", 0.3, 1.0, 0.70, 0.05, help="Share of reproductive years spent in union.")
    cc = c2.slider("Contraception (Cc)", 0.2, 1.0, 0.82, 0.05, help="1 - 1.08 × prevalence × effectiveness.")
    ca = c3.slider("Abortion (Ca)", 0.5, 1.0, 1.00, 0.05, help="Fertility-inhibiting effect of induced abortion.")
    ci = c4.slider("Infecundability (Ci)", 0.4, 1.0, 0.75, 0.05, help="Postpartum infecundability.")
    bong = compute_bongaarts_determinants(tfr=tfr_obs or 0.0, cm=cm, cc=cc, ca=ca, ci=ci)
    m_tfr = bong["modeled_tfr"]
    inhibit = (1.0 - m_tfr / bong["total_fecundity_ceiling"]) * 100.0
    cards = [("Modeled TFR", f"{m_tfr:.2f}", "children per woman"), ("Fecundity removed", f"{inhibit:.1f}%", "by the four indices together")]
    if tfr_obs:
        gap = m_tfr - tfr_obs
        cards.append(("Observed TFR", f"{tfr_obs:.2f}", f"model is {abs(gap):.2f} {'above' if gap > 0 else 'below'} it"))
    kpi_row(cards)
    st.caption("Move the sliders until the modeled and observed TFR agree to see which combination of indices fits.")

label("Reading the results", 5)
interpretations("Plain-language interpretation", measures + extra)
section_export("Section 3: Fertility & Reproduction", measures + extra, ds.name, ds.year, "S3_Fertility")
