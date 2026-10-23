"""Section 10: Cohort-component population projection."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engine.schemas import SECTION_SCHEMAS
from engine.base import DemographicMeasureResult
from engine.loader import load_demographic_dataset
from engine.projection import run_cohort_component_projection, schedule_tfr
from ui.theme import setup_page, page_header, label, notice, kpi_row, interpretations, show_plot, show_df, section_export, pill, tone_for
from ui.data_sources import sidebar_dataset, read_sample_csv
from ui.components import PALETTE

setup_page("Projections", ":material/trending_up:")
page_header("Population Projection", "Cohort-component method with low, medium and high fertility")

ds, src = sidebar_dataset("s10", SECTION_SCHEMAS["S1_COMPOSITION"], {
    "BBS Census 2022 (5-year age-sex)": ("bbs_census_2022_age_sex.csv", "BBS Census 2022"),
    "BBS Census 2011 (5-year age-sex)": ("bbs_census_2011_age_sex.csv", "BBS Census 2011"),
    "National Census 2022 (benchmark)": ("census_2022.json", "National Census 2022"),
    "National Census 2011 (benchmark)": ("census_2011.json", "National Census 2011"),
}, note="")

# ---- Assumptions file (optional)
assump = {}
with st.sidebar:
    st.markdown("**Projection assumptions**")
    use_bundled = st.checkbox("Use bundled UN WPP 2024 assumptions", value=True, key="s10_bundled")
    a_up = st.file_uploader("projection_assumptions.csv", type=["csv"], key="s10_assump")
try:
    a_df = pd.read_csv(a_up) if a_up is not None else (read_sample_csv("bbs_un_projection_assumptions.csv") if use_bundled else None)
    if a_df is not None:
        a_df.columns = [c.strip().lower() for c in a_df.columns]
        assump = {str(k).strip().lower(): float(v) for k, v in zip(a_df["indicator"], a_df["value"])}
except Exception as exc:
    st.error(f"Could not read the assumptions file: {exc}. It needs 'indicator' and 'value' columns.")
    st.stop()

base_df = ds.age_group_5yr
if base_df is None or not {"male", "female"} <= set(base_df.columns):
    notice("A male/female 5-year age table is required", "Choose a census age-sex dataset or upload one with age_group, male and female columns.", "amber")
    st.stop()

# ---- Fertility and mortality: the dataset's own when present, otherwise bundled SVRS 2022
fert, mort, notes = ds.fertility_schedule, ds.mortality_schedule, []
if fert is None or fert.empty:
    fert = load_demographic_dataset(read_sample_csv("bbs_svrs_2022_fertility.csv"), name="SVRS").fertility_schedule
    notes.append("fertility from bundled BBS SVRS 2022")
if mort is None or mort.empty:
    mort = load_demographic_dataset(read_sample_csv("bbs_svrs_2022_mortality.csv"), name="SVRS").mortality_schedule
    notes.append("mortality from bundled BBS SVRS 2022")
notice(src, f"Base population: {ds.name}" + (f". Using {' and '.join(notes)}." if notes else "."))

# ---- Controls
label("Assumptions", 1)
tfr_obs = schedule_tfr(fert)
c1, c2, c3, c4 = st.columns(4)
HORIZONS = [15, 20, 25, 30, 35, 40]
default_h = int(assump.get("horizon_years", 30))
horizon = c1.selectbox("Horizon (years)", HORIZONS, index=HORIZONS.index(default_h) if default_h in HORIZONS else 3)
scenario = c2.selectbox("Fertility scenario", ["Medium", "Low", "High"]).lower()
srb = c3.number_input("Sex ratio at birth", 100.0, 115.0, float(assump.get("srb", 105.0)), 0.5, help="Male births per 100 female births.")
mig = c4.number_input("Net migration (per year)", value=float(assump.get("net_migration_annual", 0.0)), step=10000.0, help="Positive = net inflow.")
tfr_targets = {k: assump[f"tfr_{v}_variant"] for k, v in {"low": "low", "medium": "med", "high": "high"}.items() if f"tfr_{v}_variant" in assump} or None
if tfr_targets:
    st.caption(f"Observed TFR in the schedule: {tfr_obs:.2f}. Scenario targets reached over 15 years: low {tfr_targets.get('low', '–')}, "
               f"medium {tfr_targets.get('medium', '–')}, high {tfr_targets.get('high', '–')}.")
else:
    st.caption(f"Observed TFR in the schedule: {tfr_obs:.2f}. Without target TFRs, low/medium/high scale it by 0.82 / 1.00 / 1.18 over 15 years.")

base_year = int(ds.year or assump.get("base_year", 2022))
try:
    kw = dict(base_age_sex_df=base_df, fertility_schedule=fert, mortality_schedule=mort, base_year=base_year, horizon_years=horizon,
              srb=srb, net_migration_annual=mig, tfr_targets=tfr_targets)
    active = run_cohort_component_projection(scenario=scenario, **kw)
    low = run_cohort_component_projection(scenario="low", **kw)
    high = run_cohort_component_projection(scenario="high", **kw)
except ValueError as exc:
    st.error(f"The projection could not run: {exc}")
    st.stop()

sm = active.summary_df
p0, p1 = float(sm["total_population"].iloc[0]), float(sm["total_population"].iloc[-1])
end_year = int(sm["year"].iloc[-1])
label(f"Overview {base_year} to {end_year}", 2)
kpi_row([(f"Population {base_year}", f"{p0:,.0f}", "base"), (f"Population {end_year}", f"{p1:,.0f}", f"{scenario} variant"),
         ("Change", f"{p1 - p0:+,.0f}", f"{(p1 - p0) / p0 * 100:+.1f}%"),
         (f"Working-age share {end_year}", f"{sm['pct_working_age'].iloc[-1]:.1f}%", f"Dividend: {active.dividend_status}")])

label("Results", 3)
t1, t2, t3, t4 = st.tabs(["Scenario envelope", "Age structure", "Schedule", "Policy flags"])
LAYOUT = dict(paper_bgcolor=PALETTE["bg"], plot_bgcolor=PALETTE["card"], font=dict(family="Inter, sans-serif", color=PALETTE["text"]),
              legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5), margin=dict(l=30, r=20, t=50, b=70))
with t1:
    with st.container(border=True):
        fig = go.Figure()
        fig.add_scatter(x=high.summary_df["year"], y=high.summary_df["total_population"], mode="lines", name="High", line=dict(color=PALETTE["teal"], dash="dot", width=2))
        fig.add_scatter(x=sm["year"], y=sm["total_population"], mode="lines+markers", name=f"Selected: {scenario.title()}", line=dict(color=PALETTE["male"], width=3.5))
        fig.add_scatter(x=low.summary_df["year"], y=low.summary_df["total_population"], mode="lines", name="Low", line=dict(color=PALETTE["compare_male"], dash="dash", width=2))
        fig.update_layout(title="Total population by scenario", xaxis_title="Year", yaxis_title="Population", height=400, **LAYOUT)
        show_plot(fig, key="s10_env")
with t2:
    with st.container(border=True):
        fig = go.Figure()
        for col, name, color in [("pct_working_age", "Working age (15-64)", PALETTE["male"]), ("pct_youth", "Children (0-14)", PALETTE["female"]), ("pct_elderly", "Elderly (65+)", PALETTE["compare_male"])]:
            fig.add_scatter(x=sm["year"], y=sm[col], mode="lines+markers", name=name, line=dict(color=color, width=2.6))
        fig.add_hline(y=60, line_dash="dot", line_color=PALETTE["text_light"], annotation_text="60% dividend threshold", annotation_position="bottom right")
        fig.update_layout(title="Broad age groups (% of population)", xaxis_title="Year", yaxis_title="Share (%)", height=380, **LAYOUT)
        show_plot(fig, key="s10_shares")
with t3:
    fmt = {"total_population": "{:,.0f}", "male_population": "{:,.0f}", "female_population": "{:,.0f}", "pop_0_14": "{:,.0f}", "pop_15_64": "{:,.0f}",
           "pop_65_plus": "{:,.0f}", "pct_youth": "{:.1f}", "pct_working_age": "{:.1f}", "pct_elderly": "{:.1f}", "total_dependency_ratio": "{:.1f}",
           "old_age_dependency_ratio": "{:.1f}", "tfr": "{:.2f}", "births_5yr": "{:,.0f}", "deaths_5yr": "{:,.0f}"}
    show_df(sm[[c for c in fmt if c in sm.columns] + ["year"]].set_index("year").style.format(fmt, na_rep="–"), height=360)
with t4:
    st.info(active.narrative_policy_brief.replace("**", ""))
    for f in active.policy_flags:
        with st.container(border=True):
            st.html(f'<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><b>{f.title}</b>{pill(f.severity.title(), tone_for(f.severity))}</div>')
            st.write(f.description)
            st.caption(f"Trigger: {f.rationale}")
            for rec in f.policy_recommendations:
                st.markdown(f"- {rec}")
    if not active.policy_flags:
        st.success("No threshold was crossed within this horizon.")

with st.expander("Model assumptions"):
    for a in active.assumptions_summary:
        st.markdown(f"- {a}")

measures = [
    DemographicMeasureResult(code="PROJ_HORIZON", shortform="Horizon", full_name="Projection Horizon", name="Projection Horizon (years)", block="Projection",
                             raw_value=float(horizon), formatted_value=f"{horizon} years ({base_year}-{end_year})", unit="years", formula="5-year steps",
                             citation="Preston et al. (2001), Ch. 6", plain_interpretation=f"Cohort-component projection from {base_year} to {end_year}."),
    DemographicMeasureResult(code="PROJ_POP_END", shortform="P_end", full_name="Projected Total Population", name=f"Projected Total Population ({end_year})", block="Projection",
                             raw_value=p1, formatted_value=f"{p1:,.0f} persons", unit="persons", formula="Cohort-component simulation", citation="UN WPP methodology",
                             plain_interpretation=f"Under the {scenario} variant the population reaches {p1:,.0f} by {end_year} ({p1 - p0:+,.0f})."),
    DemographicMeasureResult(code="PROJ_WORK_SHARE", shortform="%15-64", full_name="Working-Age Share", name=f"Working-Age Share ({end_year})", block="Projection",
                             raw_value=float(sm["pct_working_age"].iloc[-1]), formatted_value=f"{sm['pct_working_age'].iloc[-1]:.1f}%", unit="%",
                             formula="P(15-64) / P(total) × 100", citation="Demographic dividend threshold: 60%",
                             plain_interpretation=f"The working-age share is {sm['pct_working_age'].iloc[-1]:.1f}% in {end_year}. Dividend status: {active.dividend_status}."),
]
label("Reading the results", 4)
interpretations("Plain-language interpretation", measures, extra=[
    "The cohort-component method ages each age-sex group forward with life-table survival, adds births from age-specific fertility, and adds net migration.",
    "The demographic dividend window is when people aged 15-64 are at least 60% of the population.",
])
section_export(f"Section 10: Projection ({scenario.title()} variant)", measures, ds.name, ds.year, "S10_Projection")
