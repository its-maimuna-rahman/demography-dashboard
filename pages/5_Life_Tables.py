"""Section 5: Life tables and longevity."""
import pandas as pd
import streamlit as st

from engine.schemas import SECTION_SCHEMAS
from engine.lifetable import build_abridged_life_table, build_multiple_decrement_table, calculate_working_life_expectancy
from ui.theme import setup_page, page_header, label, notice, measure_grid, interpretations, show_plot, show_df, section_export
from ui.data_sources import sidebar_dataset
from ui.calculators import calculator_panel
from ui.components import create_life_table_curves

setup_page("Life Tables", ":material/timeline:")
page_header("Life Tables", "Survivorship, life expectancy and adult mortality")

ds, src = sidebar_dataset("s5", SECTION_SCHEMAS["S5_LIFETABLE"], {
    "BBS SVRS 2022 (mortality schedule)": ("bbs_svrs_2022_mortality.csv", "BBS SVRS 2022 Mortality"),
    "National Census 2022 (benchmark)": ("census_2022.json", "National Census 2022"),
    "National Census 2011 (benchmark)": ("census_2011.json", "National Census 2011"),
})
notice(src, f"Dataset: {ds.name}")

if ds.mortality_schedule is None or ds.mortality_schedule.empty:
    notice("A mortality schedule is required", "Upload a table with age_group, population and deaths columns (see the template in the sidebar).", "amber")
    st.stop()

try:
    lt_df, indicators = build_abridged_life_table(ds.mortality_schedule)
except Exception as exc:
    st.error(f"Could not build a life table from this mortality schedule: {exc}")
    st.stop()
measures = list(indicators.values())

label("Key indicators", 1)
measure_grid(measures)

label("Survivorship and life expectancy", 2)
with st.container(border=True):
    show_plot(create_life_table_curves(lt_df, title=f"Abridged life table: {ds.name}"), key="s5_curves")

label("Tables", 3)
t1, t2, t3 = st.tabs(["Abridged life table", "Cause elimination", "Working life"])
with t1:
    fmt = {"lx": "{:,.0f}", "ndx": "{:,.0f}", "nLx": "{:,.0f}", "Tx": "{:,.0f}", "ex": "{:.2f}",
           "nMx": "{:.4f}", "nqx": "{:.4f}", "npx": "{:.4f}", "nax": "{:.2f}"}
    show_df(lt_df.style.format({k: v for k, v in fmt.items() if k in lt_df.columns}, na_rep="open"), hide_index=True)
with t2:
    cause_cols = [c for c in ds.mortality_schedule.columns if c not in ("age_group", "population", "deaths", "asdr")]
    if cause_cols:
        _, gains = build_multiple_decrement_table(ds.mortality_schedule, cause_columns=cause_cols)
        for k, v in gains.items():
            st.markdown(f"**{k.replace('gain_if_eliminated_', '').replace('_', ' ').title()}**: removing this cause adds {v:.2f} years to e0.")
    else:
        notice("No cause-of-death columns in this dataset",
               "Add one column of deaths per cause (same age groups) to the mortality table to see life-expectancy gains from eliminating each cause.")
with t3:
    st.caption("Activity rates below are illustrative placeholders. Replace them with labour-force participation rates for your population.")
    default_rates = pd.DataFrame({"from_age": [0, 15, 25, 55, 65], "activity_rate": [0.0, 0.58, 0.84, 0.68, 0.22]})
    edited = st.data_editor(default_rates, hide_index=True, num_rows="dynamic", key="s5_rates")
    rates = {int(r.from_age): float(r.activity_rate) for r in edited.dropna().itertuples()}
    if rates:
        wlt = calculate_working_life_expectancy(lt_df, rates)
        show_df(wlt[["x", "lx", "activity_rate", "working_nLx", "Tw_x", "working_ex"]].style.format(
            {"lx": "{:,.0f}", "activity_rate": "{:.0%}", "working_nLx": "{:,.0f}", "Tw_x": "{:,.0f}", "working_ex": "{:.2f}"}), hide_index=True)

label("Reed-Merrell person-years", 4)
st.caption("Person-years for the first age intervals from survivors l(x). l(0) starts at the radix; l(5) and l(10) are filled from the table above when it has those ages.")
lt_defaults = {"l0": 100000.0}
for age in (5, 10):
    row = lt_df[lt_df["x"] == age]
    if not row.empty:
        lt_defaults[f"l{age}"] = float(row.iloc[0]["lx"])
extra = calculator_panel("lifetable", ds, defaults=lt_defaults, prefix="s5")

label("Reading the results", 5)
interpretations("Plain-language interpretation", measures + extra)
section_export("Section 5: Life Tables", measures + extra, ds.name, ds.year, "S5_LifeTable")
