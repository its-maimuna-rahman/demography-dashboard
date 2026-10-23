"""Section 9: Stable and stationary populations."""
import math
import re
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engine.schemas import SECTION_SCHEMAS
from engine.base import DemographicMeasureResult
from engine.lifetable import build_abridged_life_table
from engine.loader import load_demographic_dataset
from engine.stable import (solve_lotka_intrinsic_r, compute_stable_population_measures,
                           calculate_leslie_dominant_eigenvalue, calculate_keyfitz_population_momentum)
from ui.theme import setup_page, page_header, label, notice, kpi_row, measure_grid, interpretations, show_plot, show_df, section_export
from ui.data_sources import sidebar_dataset, read_sample_csv, load_sample
from ui.components import PALETTE

setup_page("Stable Population", ":material/balance:")
page_header("Stable Population", "Lotka renewal, intrinsic rates and population momentum")

ds, src = sidebar_dataset("s9", SECTION_SCHEMAS["S9_STABLE"], {
    "BBS SVRS 2022 (fertility schedule)": ("bbs_svrs_stable_population.csv", "BBS SVRS 2022 Stable Population"),
    "National Census 2022 (benchmark)": ("census_2022.json", "National Census 2022"),
    "National Census 2011 (benchmark)": ("census_2011.json", "National Census 2011"),
})

# ---- Mortality schedule: dataset's own, bundled, or uploaded
with st.sidebar:
    st.markdown("**Mortality schedule**")
    opts = (["From the fertility dataset"] if ds.mortality_schedule is not None else []) + ["Bundled BBS SVRS 2022", "Upload my own"]
    mort_src = st.radio("Mortality source", opts, label_visibility="collapsed", key="s9_mort")
    mort_up = st.file_uploader("mortality_age_sex.csv", type=["csv"], key="s9_mort_up") if mort_src == "Upload my own" else None

if mort_src == "From the fertility dataset":
    mort, mort_note = ds.mortality_schedule, "dataset's own mortality schedule"
elif mort_src == "Upload my own":
    if mort_up is None:
        notice("Upload a mortality schedule", "Columns: age_group, population, deaths.", "amber")
        st.stop()
    try:
        mort = load_demographic_dataset(mort_up, name="Uploaded mortality").mortality_schedule
    except Exception as exc:
        st.error(f"Could not read the mortality file: {exc}")
        st.stop()
    mort_note = f"uploaded file {mort_up.name}"
else:
    mort, mort_note = load_sample("bbs_svrs_2022_mortality.csv", "BBS SVRS 2022 Mortality").mortality_schedule, "bundled BBS SVRS 2022 schedule"

fert = ds.fertility_schedule
if fert is None or fert.empty or mort is None or len(mort) == 0:
    notice("Both a fertility and a mortality schedule are required", "Fertility needs age_group, female_pop, births. Mortality needs age_group, population, deaths.", "amber")
    st.stop()
notice(src, f"Fertility: {ds.name}. Mortality: {mort_note}.")

try:
    stable = compute_stable_population_measures(fert, mort)
    lt, _ = build_abridged_life_table(mort, sex="female")
    sol = solve_lotka_intrinsic_r(fert, lt)
except Exception as exc:
    st.error(f"Could not solve the Lotka equation with these schedules: {exc}")
    st.stop()
r = sol["intrinsic_r"]
leslie = calculate_leslie_dominant_eigenvalue(r)
e0 = float(lt["ex"].iloc[0])

# Current crude birth rate for Keyfitz momentum (only from real inputs)
births_total = ds.total_live_births if ds.total_live_births else float(fert["births"].sum())
pop_total = ds.total_population or (float(mort["population"].sum()) if "population" in mort.columns else None)
momentum = None
if births_total and pop_total:
    momentum = calculate_keyfitz_population_momentum(crude_birth_rate=births_total / pop_total * 1000.0, life_expectancy_e0=e0, nrr=sol["nrr"])

label("Core indicators", 1)
core = [stable[c] for c in ["LOTKA_R", "INTRINSIC_B", "INTRINSIC_D", "GEN_LEN"] if c in stable]
measure_grid(core)

label("Moments and quadratic approximation", 2)
measure_grid([stable[c] for c in ["R1", "R2", "MU", "ALPHA", "BETA", "R_QUAD", "T_QUAD"] if c in stable])
st.caption("The quadratic approximation solves ½βr² + αr − ln R0 = 0 using the first two moments of the net maternity function. Compare r(quad) with the exact Lotka root above.")

label("Methods", 3)
t1, t2, t3, t4 = st.tabs(["Lotka and stationary", "Stable age distribution", "Leslie eigenvalue", "Keyfitz momentum"])

with t1:
    st.markdown("**Lotka renewal parameters**")
    kpi_row([("Net reproduction rate (R0)", f"{sol['nrr']:.3f}", "daughters per woman"),
             ("Mean length of generation (T)", f"{sol['mean_length_generation_years']:.1f} years", "ln R0 / r"),
             ("Mean age at childbearing (μ)", f"{sol['r1'] / sol['nrr']:.1f} years" if sol["nrr"] else "n/a", "R1 / R0")])
    st.markdown("**Stationary equilibrium (r = 0)**")
    kpi_row([("Life expectancy at birth (e0)", f"{e0:.1f} years"),
             ("Stationary birth rate", f"{1000.0 / e0:.2f}", "per 1,000, equal to 1 / e0"),
             ("Stationary death rate", f"{1000.0 / e0:.2f}", "per 1,000, equal to 1 / e0")])

with t2:
    b = sol["intrinsic_birth_rate_per_1000"] / 1000.0
    labels, shares = [], []
    for _, row in lt.iterrows():
        lbl = str(row["age_group"])
        nums = [float(x) for x in re.findall(r"\d+", lbl)]
        mid = (nums[0] + nums[-1] + 1) / 2.0 if len(nums) > 1 else (nums[0] + 2.5 if nums else 40.0)
        labels.append(lbl)
        shares.append(b * math.exp(-r * mid) * float(row["nLx"]) / 100000.0)
    arr = np.array(shares)
    stable_pct = arr / arr.sum() * 100.0
    obs_df = ds.age_group_5yr if ds.age_group_5yr is not None else load_sample("bbs_census_2022_age_sex.csv").age_group_5yr
    obs_note = "" if ds.age_group_5yr is not None else "Observed bars come from the bundled BBS Census 2022 table."
    tc = "total" if "total" in obs_df.columns else obs_df.columns[1]
    obs = []
    for lbl in labels:
        m = obs_df[obs_df["age_group"].astype(str) == lbl]
        obs.append(float(m[tc].iloc[0]) / float(obs_df[tc].sum()) * 100.0 if not m.empty else np.nan)
    fig = go.Figure()
    fig.add_bar(name="Observed population (%)", x=labels, y=obs, marker_color=PALETTE["female"])
    fig.add_scatter(name="Stable distribution (%)", x=labels, y=stable_pct, mode="lines+markers", line=dict(color=PALETTE["male"], width=3))
    fig.update_layout(paper_bgcolor=PALETTE["bg"], plot_bgcolor=PALETTE["card"], height=400, xaxis_title="Age group", yaxis_title="Share of population (%)",
                      font=dict(family="Inter, sans-serif", color=PALETTE["text"]), legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5), margin=dict(l=30, r=20, t=30, b=80))
    show_plot(fig, key="s9_stable")
    st.caption("Under constant rates any age structure converges to the stable one: c(a) = b · exp(−r·a) · p(a). " + obs_note)

with t3:
    kpi_row([("Dominant eigenvalue (λ)", f"{leslie['dominant_eigenvalue_lambda']:.5f}", "5-year multiplier, exp(5r)"),
             ("Annual multiplier", f"{leslie['annual_multiplier']:.5f}"), ("Long-run regime", leslie["asymptotic_state"])])
    st.caption("λ > 1: the population grows without limit; λ = 1: stationary; λ < 1: it shrinks toward zero.")

with t4:
    if momentum:
        kpi_row([("Momentum factor (M)", f"{momentum['momentum_multiplier']:.3f}", "M = b · e0 / √NRR"),
                 ("Growth built into age structure", f"{momentum['ultimate_growth_percent']:+.1f}%")])
        st.write(momentum["interpretation"])
        st.caption(f"Inputs: crude birth rate {momentum['initial_cbr']:.1f} per 1,000, e0 {momentum['initial_e0']:.1f} years, NRR {momentum['initial_nrr']:.3f}. "
                   "This is Keyfitz's short-form approximation.")
    else:
        notice("Momentum needs a crude birth rate", "Births and a total population are required. Use a dataset with both, or a mortality schedule that includes population.", "amber")

measures = list(stable.values()) + [DemographicMeasureResult(
    code="LESLIE_LAMBDA", shortform="λ", full_name="Leslie Dominant Eigenvalue", name="Leslie Dominant Eigenvalue (λ)", block="Stable Population",
    raw_value=leslie["dominant_eigenvalue_lambda"], formatted_value=f"{leslie['dominant_eigenvalue_lambda']:.5f}", unit="multiplier", formula="λ = exp(5r)",
    citation="Preston et al. (2001), Ch. 6-7",
    plain_interpretation=f"The 5-year long-run growth multiplier is {leslie['dominant_eigenvalue_lambda']:.5f}, a {leslie['asymptotic_state'].lower()} regime.")]
if momentum:
    measures.append(DemographicMeasureResult(
        code="KEYFITZ_M", shortform="M", full_name="Keyfitz Population Momentum", name="Keyfitz Population Momentum (M)", block="Stable Population",
        raw_value=momentum["momentum_multiplier"], formatted_value=f"{momentum['momentum_multiplier']:.3f}", unit="factor", formula="M = b · e0 / sqrt(NRR)",
        citation="Keyfitz (1971)", plain_interpretation=momentum["interpretation"]))

label("Reading the results", 4)
interpretations("Plain-language interpretation", measures, extra=[
    "A stable population has a fixed age distribution and grows at a constant rate r. A stationary population is the special case r = 0, where birth and death rates both equal 1/e0.",
])
section_export("Section 9: Stable & Stationary Populations", measures, ds.name, ds.year, "S9_Stable")
