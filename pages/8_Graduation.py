"""Section 8: Graduation and age smoothing."""
import re
import pandas as pd
import streamlit as st

from engine.schemas import SECTION_SCHEMAS
from engine.base import DemographicMeasureResult
from engine.graduation import (graduate_5yr_to_single_year_sprague, graduate_5yr_to_single_year_beers,
                               graduate_karup_king_with_diagnostics, carrier_farrag_smoothing)
from ui.theme import setup_page, page_header, label, notice, kpi_row, interpretations, show_plot, show_df, section_export
from ui.data_sources import sidebar_dataset
from ui.components import create_sprague_graduation_chart

setup_page("Graduation", ":material/stacked_line_chart:")
page_header("Graduation", "Splitting 5-year age groups into single years")

ds, src = sidebar_dataset("s8", SECTION_SCHEMAS["S8_GRADUATION"], {
    "BBS Census 2022 (5-year age-sex)": ("bbs_census_2022_age_sex.csv", "BBS Census 2022"),
    "BBS Census 2011 (5-year age-sex)": ("bbs_census_2011_age_sex.csv", "BBS Census 2011"),
    "National Census 2022 (benchmark)": ("census_2022.json", "National Census 2022"),
    "National Census 2011 (benchmark)": ("census_2011.json", "National Census 2011"),
})
notice(src, f"Dataset: {ds.name}")

tbl = ds.age_group_5yr
if tbl is None or tbl.empty:
    notice("A 5-year age table is required", "Upload a table with age_group and total (or male and female) columns.", "amber")
    st.stop()
tbl = tbl.reset_index(drop=True)
if "total" in tbl.columns:
    counts_all = tbl["total"].astype(float).tolist()
elif {"male", "female"} <= set(tbl.columns):
    counts_all = (tbl["male"] + tbl["female"]).astype(float).tolist()
else:
    st.error("The age table needs a 'total' column, or 'male' and 'female' columns.")
    st.stop()
labels = tbl["age_group"].astype(str).tolist()
open_last = labels[-1].strip().endswith("+")
first = re.match(r"^(\d+)", labels[0])
start_age = int(first.group(1)) if first else 0
closed = counts_all[:-1] if open_last else counts_all
if len(closed) < 5:
    st.error("Graduation needs at least five closed 5-year groups.")
    st.stop()

label("Method", 1)
method = st.radio("Graduation method", [
    "Sprague osculatory (published multipliers)",
    "Karup-King-type (cubic through cumulative counts)",
    "Beers-type (monotone cubic through cumulative counts)",
    "1-2-1 smoothing, then Sprague",
], horizontal=False, label_visibility="collapsed")
if "Beers" in method:
    st.caption("Beers-type uses a monotone cubic through cumulative counts. It is not the published Beers coefficient table.")
if "Karup" in method:
    st.caption("Karup-King-type is derived from a cubic through four cumulative boundaries.")
if "1-2-1" in method:
    st.caption("1-2-1 smoothing averages each group with its neighbours (weights 1, 2, 1) and keeps the total unchanged.")

if "Sprague osculatory" in method:
    grad, diag = graduate_5yr_to_single_year_sprague(counts_all, start_age, open_last_group=open_last)
elif "Karup" in method:
    grad, diag = graduate_karup_king_with_diagnostics(counts_all, start_age, open_last_group=open_last)
elif "Beers" in method:
    grad, diag = graduate_5yr_to_single_year_beers(counts_all, start_age, open_last_group=open_last)
else:
    smooth = carrier_farrag_smoothing(closed)
    grad, diag = graduate_5yr_to_single_year_sprague(smooth, start_age)
    diag["open_interval_total"] = counts_all[-1] if open_last else None
    diag["method"] = "1-2-1 smoothing + Sprague"
    diag["interpretation"] = "Groups were smoothed with 1-2-1 weights, then split into single years with Sprague. Totals of the smoothed groups are conserved, not the originals."
method_name = diag["method"]

label("Diagnostics", 2)
shown_orig = float(sum(closed))
kpi_row([
    ("Closed 5-year groups", f"{len(closed)}", f"{shown_orig:,.0f} persons"),
    ("Single-year ages", f"{len(grad)}", f"{grad['graduated_population'].sum():,.0f} persons"),
    ("Largest group difference", f"{diag['max_group_re_sum_difference']:.4f}", "persons, target 0"),
    ("Re-sum check", "Passed" if diag["re_sum_verified"] else "Check", "each group re-sums to its input"),
])
if open_last:
    st.caption(f"The open-ended group ({labels[-1]}, {counts_all[-1]:,.0f} persons) is kept as one interval and is not split.")
if "1-2-1" in method:
    st.caption("With 1-2-1 smoothing the re-sum check compares against the smoothed groups, so the total can differ slightly from the original.")

label("Original steps and graduated curve", 3)
with st.container(border=True):
    show_plot(create_sprague_graduation_chart(closed if "1-2-1" not in method else smooth, grad, start_age=start_age,
                                              title=f"{method_name}: 5-year steps and single-year estimates"), key="s8_chart")

label("Tables", 4)
t1, t2 = st.tabs(["Single-year estimates", "Group conservation audit"])
with t1:
    show_df(grad.style.format({"graduated_population": "{:,.1f}"}), hide_index=True, height=360)
with t2:
    base = smooth if "1-2-1" in method else closed
    rows = []
    for i, w in enumerate(base):
        s = float(grad["graduated_population"].iloc[i * 5:(i + 1) * 5].sum())
        rows.append({"Group": f"{start_age + i * 5}-{start_age + i * 5 + 4}", "Input": round(w, 1),
                     "Sum of 5 single years": round(s, 1), "Difference": round(s - w, 4),
                     "Status": "Conserved" if abs(s - w) < 0.05 else "Discrepancy"})
    show_df(pd.DataFrame(rows), hide_index=True)

measures = [
    DemographicMeasureResult(code="GRAD_METHOD", shortform="Method", full_name="Graduation Technique", name=f"Graduation Technique ({method_name})",
                             block="Graduation", raw_value=1.0, formatted_value=method_name, unit="technique", formula="Osculatory / cumulative interpolation",
                             citation="Sprague (1880); Shryock & Siegel (1976), Ch. 22", plain_interpretation=diag["interpretation"]),
    DemographicMeasureResult(code="RESUM_ERROR", shortform="max group diff", full_name="Largest Group Re-sum Difference", name="Largest Group Re-sum Difference",
                             block="Graduation", raw_value=diag["max_group_re_sum_difference"], formatted_value=f"{diag['max_group_re_sum_difference']:.4f} persons",
                             unit="persons", formula="max_i |sum(single years in group i) - W_i|", citation="Actuarial conservation property",
                             plain_interpretation="How far any single 5-year group moved after graduation. Zero means every group total was kept."),
]
label("Reading the results", 5)
interpretations("Plain-language interpretation", measures, extra=[
    "Osculatory interpolation joins neighbouring groups with smooth curves, so the single-year ages show no artificial steps at group boundaries.",
])
section_export(f"Section 8: Graduation ({method_name})", measures, ds.name, ds.year, "S8_Graduation")
