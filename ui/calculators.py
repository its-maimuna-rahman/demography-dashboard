"""Interactive calculators for the measures from the class revision sheet."""

from __future__ import annotations
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import streamlit as st

from engine import extra_measures as xm
from engine.registry import MEASURES_CATALOGUE
from ui.theme import result_card, measure_grid, show_df, notice, kpi_row
from ui.data_sources import read_sample_csv


def _fmt(default: float) -> str:
    return "%.0f" if default >= 1000 else "%.2f"


def _number(label: str, default: float, key: str, help_text: str = "") -> float:
    return float(st.number_input(label, min_value=0.0, value=float(default), step=1.0, format=_fmt(default), key=key, help=help_text or None))


def calculator_panel(section: str, ds, defaults: Optional[Dict[str, float]] = None, prefix: Optional[str] = None) -> List[Any]:
    """Draw every calculator of a section in pill tabs, one per group. Returns the results that are complete."""
    specs = xm.CALCULATORS.get(section, [])
    if not specs:
        return []
    prefix = prefix or section
    groups: List[str] = []
    for sp in specs:
        if sp.group not in groups:
            groups.append(sp.group)
    done: List[Any] = []
    tabs = st.tabs(groups) if len(groups) > 1 else [st.container()]
    for tab, group in zip(tabs, groups):
        with tab:
            for sp in [x for x in specs if x.group == group]:
                meta = MEASURES_CATALOGUE[sp.code]
                with st.container(border=True):
                    st.markdown(f"**{meta['full_name']}**")
                    if sp.note:
                        st.caption(sp.note)
                    cols = st.columns(min(len(sp.inputs), 4))
                    vals: Dict[str, float] = {}
                    for i, inp in enumerate(sp.inputs):
                        default = inp.default
                        if defaults and inp.key in defaults and defaults[inp.key]:
                            default = defaults[inp.key]
                        elif inp.prefill is not None:
                            try:
                                pv = inp.prefill(ds)
                            except Exception:
                                pv = None
                            if pv:
                                default = float(pv)
                        with cols[i % len(cols)]:
                            vals[inp.key] = _number(inp.label, default, f"{prefix}_{sp.code}_{inp.key}_{getattr(ds, 'name', '')}", inp.help)
                    # A result only counts once every figure the user must supply has been entered (inputs that start at 0).
                    entered = all(vals[inp.key] > 0 for inp in sp.inputs if inp.default == 0.0)
                    res = xm.evaluate(sp, vals) if entered else None
                    result_card(res, meta["shortform"], meta["full_name"])
                    if res is not None:
                        done.append(res)
    return done


# ---------------------------------------------------------------- special panels
CLASS_NOTES_EXAMPLE = pd.DataFrame({"year": [1959, 1960, 1961], "deaths": [10176, 10063, 9726], "population": [1126000, 1171000, 1225000]})


def multi_year_cdr_panel(prefix: str = "mycdr") -> List[Any]:
    st.caption("Enter one row per year (3 or 5 years are typical). The rows start with the worked example from the class notes (1959-61); replace them with your own.")
    df = st.data_editor(CLASS_NOTES_EXAMPLE, hide_index=True, num_rows="dynamic", key=f"{prefix}_table",
                        column_config={"year": st.column_config.NumberColumn("Year", format="%d"),
                                       "deaths": st.column_config.NumberColumn("Deaths", format="%d"),
                                       "population": st.column_config.NumberColumn("Population", format="%d")})
    d = df.dropna(subset=["deaths", "population"])
    res = xm.multi_year_cdr(d["deaths"].tolist(), d["population"].tolist()) if len(d) >= 2 else None
    if not res:
        notice("Add at least two years with a positive population", tone="amber")
        return []
    cards = [xm.make_result(c, v, {"years": int(len(d))}) for c, v in res.items()]
    measure_grid(cards)
    st.caption("Version 3 divides by the mid-period population: the middle year if the number of years is odd, or the average of the two middle years if it is even.")
    return cards


def _bundled_total(file: str) -> float:
    return float(read_sample_csv(file)["total"].sum())


def percentage_change_panel(ds, prefix: str = "pct") -> List[Any]:
    old_def = _bundled_total("bbs_census_2011_age_sex.csv")
    new_def = float(ds.total_population or 0.0)
    old = _number("Old value (default: BBS Census 2011 total)", old_def, f"{prefix}_old")
    new = _number("New value (default: this dataset's total)", new_def, f"{prefix}_new_{getattr(ds, 'name', '')}")
    chg = xm.percentage_change(old, new) if old > 0 else None
    result_card(xm.make_result("PCT_CHANGE", chg, {"old": old, "new": new}) if chg is not None else None, "%Δ", "Percentage Change")
    return [xm.make_result("PCT_CHANGE", chg, {"old": old, "new": new})] if chg is not None else []


def age_distribution_comparison_panel(ds, prefix: str = "dist") -> List[Any]:
    options = {"BBS Census 2011": "bbs_census_2011_age_sex.csv", "BBS Census 2022": "bbs_census_2022_age_sex.csv"}
    tbl = ds.age_group_5yr
    if tbl is None or "total" not in tbl.columns:
        notice("This dataset has no 5-year age table", "The index of dissimilarity needs percentage distributions by age group.", "amber")
        return []
    choice = st.selectbox("Compare this dataset's age distribution with", list(options), key=f"{prefix}_cmp")
    other = read_sample_csv(options[choice])
    merged = tbl[["age_group", "total"]].astype({"age_group": str}).merge(other[["age_group", "total"]].astype({"age_group": str}), on="age_group", suffixes=("_1", "_2"))
    if merged.empty:
        notice("The age groups do not line up", "Both tables need the same 5-year groups.", "amber")
        return []
    r1, r2 = xm.percent_distribution(merged["total_1"]), xm.percent_distribution(merged["total_2"])
    ird = xm.index_of_relative_difference(r1, r2)
    id_val = xm.index_of_dissimilarity(r1, r2)
    top = int(np.nanargmax(ird))
    cards = [xm.make_result("ID", id_val, {"compared_with": choice}),
             xm.make_result("IRD", float(ird[top]), {"age_group": merged.loc[top, "age_group"], "compared_with": choice})]
    measure_grid(cards)
    st.caption(f"Index of relative difference is largest in the {merged.loc[top, 'age_group']} age group. r1 is this dataset, r2 is {choice}.")
    out = pd.DataFrame({"Age group": merged["age_group"], "r1 (%)": r1.round(2), "r2 (%)": r2.round(2), "IRD": ird.round(2)})
    show_df(out, hide_index=True)
    return cards


def aabr_panel(ds, prefix: str = "aabr") -> List[Any]:
    """Direct and indirect age-adjusted birth rates against a standard population and schedule."""
    sched = ds.fertility_schedule
    if sched is None or sched.empty:
        notice("A fertility schedule is required", "Age-adjusted birth rates need women and births by age group.", "amber")
        return []
    std_fert = read_sample_csv("bbs_svrs_2022_fertility.csv")
    std_pop = read_sample_csv("bbs_census_2022_age_sex.csv")
    groups = list(sched["age_group"].astype(str))
    std_asfr = {str(r.age_group): r.births / r.female_pop for r in std_fert.itertuples() if r.female_pop > 0}
    std_women = {str(r.age_group): float(r.female) for r in std_pop.itertuples()}
    std_total_def = float(std_pop["total"].sum())
    std_cbr_def = float(std_fert["births"].sum()) / std_total_def * 1000.0
    st.caption("The standard defaults to the bundled BBS 2022 census population and SVRS fertility schedule. Edit any value to use your own standard.")
    table = pd.DataFrame({
        "age_group": groups,
        "study_births": sched["births"].astype(float).tolist(),
        "study_women": sched["female_pop"].astype(float).tolist(),
        "standard_asfr_per_woman": [round(std_asfr.get(g, 0.0), 6) for g in groups],
        "standard_women": [std_women.get(g, 0.0) for g in groups],
    })
    ed = st.data_editor(table, hide_index=True, key=f"{prefix}_{getattr(ds, 'name', '')}_table", disabled=["age_group"])
    c1, c2 = st.columns(2)
    p_std = _number("Standard total population (all ages, both sexes)", std_total_def, f"{prefix}_std_total")
    f_std = _number("Standard crude birth rate (per 1,000)", std_cbr_def, f"{prefix}_std_cbr")
    study_asfr = (ed["study_births"] / ed["study_women"].where(ed["study_women"] > 0)).fillna(0.0)
    direct = xm.aabr_direct(study_asfr, ed["standard_women"], p_std)
    indirect = xm.aabr_indirect(float(ed["study_births"].sum()), f_std, ed["standard_asfr_per_woman"], ed["study_women"])
    a, b = st.columns(2)
    with a:
        result_card(xm.make_result("AABR_D", direct, {"standard_total": p_std}) if direct is not None else None, "AABR", "Age-Adjusted Birth Rate (direct)")
    with b:
        result_card(xm.make_result("AABR_I", indirect, {"standard_cbr": f_std}) if indirect is not None else None, "AABR(ind)", "Age-Adjusted Birth Rate (indirect)")
    out: List[Any] = []
    if direct is not None:
        out.append(xm.make_result("AABR_D", direct, {"standard_total": p_std}))
    if indirect is not None:
        out.append(xm.make_result("AABR_I", indirect, {"standard_cbr": f_std}))
    return out


def total_marriage_rate_panel(ds, prefix: str = "tmr") -> List[Any]:
    st.caption("Enter marriages and women by age. Use single years of age, or 5-year groups with width 5 (the sum of age-specific rates is then multiplied by 5).")
    tbl = ds.age_group_5yr
    groups = ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49"]
    women = [0.0] * len(groups)
    if tbl is not None and "female" in tbl.columns:
        lookup = dict(zip(tbl["age_group"].astype(str), tbl["female"].astype(float)))
        women = [lookup.get(g, 0.0) for g in groups]
    df = pd.DataFrame({"age_group": groups, "marriages_women": [0.0] * len(groups), "first_marriages_women": [0.0] * len(groups), "women": women})
    ed = st.data_editor(df, hide_index=True, key=f"{prefix}_{getattr(ds, 'name', '')}_table", disabled=["age_group"])
    width = _number("Age-group width (years)", 5.0, f"{prefix}_width")
    ok = (ed["women"] > 0).all()
    a, b = st.columns(2)
    tmr = xm.total_rate(ed["marriages_women"], ed["women"], width) if ok and ed["marriages_women"].sum() > 0 else None
    tfmr = xm.total_rate(ed["first_marriages_women"], ed["women"], width) if ok and ed["first_marriages_women"].sum() > 0 else None
    with a:
        result_card(xm.make_result("TMR", tmr, {"width": width}) if tmr is not None else None, "TMR", "Total Marriage Rate (women)")
    with b:
        result_card(xm.make_result("TFMR", tfmr, {"width": width}) if tfmr is not None else None, "TFMR", "Total First Marriage Rate (women)")
    out: List[Any] = []
    if tmr is not None:
        out.append(xm.make_result("TMR", tmr, {"width": width}))
    if tfmr is not None:
        out.append(xm.make_result("TFMR", tfmr, {"width": width}))
    return out
