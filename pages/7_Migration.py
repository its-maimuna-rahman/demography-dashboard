"""Section 7: Migration and spatial redistribution."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engine.schemas import SECTION_SCHEMAS
from engine.extra_measures import compute_migration_extras
from engine.migration import calculate_migration_rates, calculate_origin_destination_matrix, calculate_survival_ratio_migration
from ui.theme import setup_page, page_header, label, notice, kpi_row, measure_grid, interpretations, show_plot, show_df, section_export
from ui.data_sources import sidebar_dataset, read_sample_csv
from ui.components import PALETTE

setup_page("Migration", ":material/route:")
page_header("Migration", "Flow rates, the balancing equation and origin-destination streams")

ds, src = sidebar_dataset("s7", SECTION_SCHEMAS["S7_MIGRATION"], {
    "BBS SVRS 2022 (migration totals)": ("bbs_svrs_2022_migration_totals.csv", "BBS SVRS 2022 Migration"),
})
notice(src, f"Dataset: {ds.name}")

in_m, out_m, pop = ds.in_migrants, ds.out_migrants, ds.total_population
if in_m is None or out_m is None or not pop:
    notice("Migration totals are incomplete",
           "The file needs in_migrants, out_migrants and midyear_population (or total_population) rows. See the template in the sidebar.", "amber")
    st.stop()

rates = calculate_migration_rates(in_migrants=in_m, out_migrants=out_m, midyear_population=pop, per=1000)
_ex = compute_migration_extras(in_m, out_m, pop)
measures = list(rates.values()) + [_ex[k] for k in ['IMRG', 'OMRG', 'GROSS_MIG', 'NET_MIG', 'MER_SIGNED'] if k in _ex]
net, gross = in_m - out_m, in_m + out_m

label("Core indicators", 1)
kpi_row([("In-migrants (input)", f"{in_m:,.0f}"), ("Out-migrants (input)", f"{out_m:,.0f}"), ("Mid-year population (input)", f"{pop:,.0f}")])
st.write("")
measure_grid(measures)

label("Methods", 2)
t_flow, t_bal, t_od, t_surv = st.tabs(["Flows", "Balancing equation", "Origin-destination", "Cohort survival"])

with t_flow:
    with st.container(border=True):
        fig = go.Figure(go.Bar(x=["In-migration", "Out-migration", "Net balance", "Gross turnover"], y=[in_m, out_m, net, gross],
                               marker_color=[PALETTE["male"], PALETTE["female"], PALETTE["compare_male"], PALETTE["compare_female"]]))
        fig.update_layout(title="Migration stream volumes", paper_bgcolor=PALETTE["bg"], plot_bgcolor=PALETTE["card"], height=340,
                          font=dict(family="Inter, sans-serif", color=PALETTE["text"]), margin=dict(l=30, r=20, t=50, b=30))
        show_plot(fig, key="s7_flow")

with t_bal:
    st.caption("P2 − P1 = (births − deaths) + net migration. Net migration is the residual.")
    p1_def = float(ds.previous_census_pop or 0.0)
    c1, c2, c3 = st.columns(3)
    p1 = c1.number_input("Population at earlier census (P1)", min_value=0.0, value=p1_def, step=100000.0)
    p2 = c2.number_input("Population at later census (P2)", min_value=0.0, value=float(pop), step=100000.0)
    years = c3.number_input("Years between censuses", min_value=1, max_value=30, value=11)
    annual_b, annual_d = ds.total_live_births, ds.total_deaths
    if annual_b is None or annual_d is None:
        notice("Births and deaths are not in this file", "Enter intercensal totals below.", "amber")
    c4, c5 = st.columns(2)
    births = c4.number_input("Intercensal births", min_value=0.0, value=float((annual_b or 0.0) * years), step=100000.0,
                             help="Default = annual births in the file × years between censuses. Replace with registered totals if you have them.")
    deaths = c5.number_input("Intercensal deaths", min_value=0.0, value=float((annual_d or 0.0) * years), step=100000.0)
    if p1 > 0 and p2 > 0:
        growth, natural = p2 - p1, births - deaths
        kpi_row([("Total change (P2 − P1)", f"{growth:+,.0f}"), ("Natural increase", f"{natural:+,.0f}"), ("Residual net migration", f"{growth - natural:+,.0f}")])
        st.caption("A negative residual means more people left than arrived over the period, assuming the births and deaths above are complete.")
    else:
        st.info("Enter both census populations to compute the residual.")

with t_od:
    up = st.file_uploader("Upload an origin-destination CSV (origin, destination, migrants)", type=["csv"], key="s7_od")
    try:
        od_df = pd.read_csv(up) if up is not None else read_sample_csv("bbs_census_2022_division_od_matrix.csv")
        od = calculate_origin_destination_matrix(od_df)
    except Exception as exc:
        st.error(f"Could not read the origin-destination table: {exc}")
        od = None
    if od:
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown("**Flow matrix (thousands)**")
            show_df(od["od_matrix"])
        with c2:
            kpi_row([("Spatial effectiveness", f"{od['spatial_effectiveness_index']:.1f}%"),
                     ("Gross flows", f"{od['gross_interregional_flows']:,.1f}k"),
                     ("Net redistribution", f"{od['net_spatial_redistribution']:,.1f}k")])

with t_surv:
    st.caption("Edit the table to run the cohort-survival method: expected survivors = S × P1, net migrants = P2 − expected survivors. "
               "The starting values are illustrative.")
    demo = pd.DataFrame({
        "age_group": ["0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34"],
        "pop_t1": [16000000, 15500000, 15000000, 14200000, 13100000, 12000000, 11000000],
        "pop_t2": [15800000, 15900000, 15400000, 14800000, 13900000, 12600000, 11500000],
        "survival_to_next_group": [0.985, 0.992, 0.990, 0.987, 0.982, 0.978, None],
    })
    ed = st.data_editor(demo, hide_index=True, key="s7_surv")
    valid = ed.dropna(subset=["age_group", "pop_t1", "pop_t2"]).reset_index(drop=True)
    sx = valid["survival_to_next_group"].dropna().tolist()
    if len(valid) >= 2 and len(sx) >= len(valid) - 1:
        res = calculate_survival_ratio_migration(valid["pop_t1"].tolist(), valid["pop_t2"].tolist(), sx[: len(valid) - 1], valid["age_group"].tolist())
        show_df(res, hide_index=True)
    else:
        st.info("Provide at least two age groups and one survival ratio for each group except the last.")

label("Reading the results", 3)
interpretations("Plain-language interpretation", measures, extra=[
    "Residual balancing equation: net migration is whatever population change births minus deaths cannot explain.",
    "Migration efficiency ratio: values near 100% mean movement mostly one way; values near 0% mean heavy two-way exchange.",
])
section_export("Section 7: Migration", measures, ds.name, ds.year, "S7_Migration")
