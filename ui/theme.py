"""
Calm Kit design system for the Vital Stats Suite.

Palette (sampled from the reference interface study):
  sage #5F7464 · moss #A9B7A6 · mist #D9DDD6 · ivory #F4EFE8 · sand #C9BDAF
Soft rounded cards, pill buttons, quiet numbered section labels, Inter typography.
"""

from __future__ import annotations
import html
import re
from typing import Any, Iterable, List, Optional, Sequence

import pandas as pd
import streamlit as st

from engine.formulas import formula_img_html

TOKENS = {
    "bg": "#F8F2EC",
    "card": "#FCFAF7",
    "ivory": "#F4EFE8",
    "mist": "#D9DDD6",
    "moss": "#A9B7A6",
    "sand": "#C9BDAF",
    "sage": "#5F7464",
    "sage_dark": "#4B5E52",
    "text": "#2B2E2A",
    "muted": "#7C807A",
    "line": "#E8E0D6",
    "amber": "#A9803F",
    "amber_bg": "#F4EBDA",
    "rose": "#A35D56",
    "rose_bg": "#F4E2DF",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

:root{
  --vs-bg:#F8F2EC; --vs-card:#FCFAF7; --vs-ivory:#F4EFE8; --vs-mist:#D9DDD6; --vs-moss:#A9B7A6;
  --vs-sand:#C9BDAF; --vs-sage:#5F7464; --vs-sage-dark:#4B5E52; --vs-text:#2B2E2A; --vs-muted:#7C807A;
  --vs-line:#E8E0D6; --vs-shadow:0 10px 28px rgba(110,90,70,.08), 0 1px 0 rgba(255,255,255,.9) inset;
}
html, body, .stApp, [class*="css"]{ font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif !important; color:var(--vs-text); }
.stApp{ background:linear-gradient(180deg,#FAF5EF 0%,#F6EEE7 100%) !important; }
header[data-testid="stHeader"]{ background:transparent !important; }
.block-container{ max-width:1180px; padding-top:2.2rem; padding-bottom:4rem; }

/* headings */
h1,h2,h3,h4{ font-family:'Inter',system-ui,sans-serif !important; color:var(--vs-text) !important; font-weight:400 !important; letter-spacing:-.01em; }
h1{ font-size:2.1rem !important; letter-spacing:.01em; }
h2{ font-size:1.35rem !important; margin-top:1.4rem !important; }
h3{ font-size:1.08rem !important; font-weight:500 !important; }
p, li, .stMarkdown{ line-height:1.6; }
code{ background:var(--vs-ivory) !important; color:var(--vs-sage-dark) !important; border-radius:8px; padding:.1rem .4rem; font-size:.82em; }

/* bordered containers become soft cards */
div[data-testid="stVerticalBlockBorderWrapper"]{
  background:var(--vs-card) !important; border:1px solid rgba(255,255,255,.85) !important;
  border-radius:22px !important; box-shadow:var(--vs-shadow) !important; padding:.35rem .5rem;
}
div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlockBorderWrapper"]{ box-shadow:none !important; background:var(--vs-ivory) !important; }

/* native metrics */
div[data-testid="stMetric"]{ background:transparent !important; padding:.2rem .2rem; }
div[data-testid="stMetricLabel"] p{ font-size:.72rem !important; letter-spacing:.14em; text-transform:uppercase; color:var(--vs-muted) !important; font-weight:500; }
div[data-testid="stMetricValue"]{ font-weight:500 !important; font-size:1.7rem !important; color:var(--vs-text) !important; font-variant-numeric:tabular-nums; }

/* pill buttons */
.stButton>button, .stDownloadButton>button, div[data-testid="stBaseButton-secondary"], div[data-testid="stBaseButton-primary"]{
  border-radius:999px !important; padding:.55rem 1.4rem !important; font-weight:500 !important; border:1px solid var(--vs-line) !important;
  background:var(--vs-card) !important; color:var(--vs-text) !important; box-shadow:0 4px 12px rgba(110,90,70,.06) !important; transition:background .15s,border-color .15s;
}
.stButton>button:hover, .stDownloadButton>button:hover{ border-color:var(--vs-sage) !important; color:#fff !important; background:var(--vs-sage) !important; transform:translateY(-2px); box-shadow:0 8px 20px rgba(95,116,100,.28) !important; }
.stButton>button:active, .stDownloadButton>button:active{ transform:translateY(0); }
div[data-testid="stVerticalBlockBorderWrapper"]{ transition:box-shadow .18s ease, border-color .18s ease; }
div[data-testid="stVerticalBlockBorderWrapper"]:hover{ border-color:var(--vs-moss) !important; }
.vs-gauge{ transition:transform .18s ease, box-shadow .18s ease; }
.vs-gauge:hover{ transform:translateY(-2px); box-shadow:0 14px 32px rgba(95,116,100,.16); }
.stButton>button[kind="primary"], .stDownloadButton>button[kind="primary"]{ background:var(--vs-sage) !important; color:#fff !important; border-color:var(--vs-sage) !important; }

/* inputs */
div[data-baseweb="select"]>div, div[data-baseweb="input"]>div, div[data-testid="stNumberInputContainer"], textarea{
  border-radius:16px !important; background:var(--vs-card) !important; border-color:var(--vs-line) !important;
}
div[data-testid="stFileUploaderDropzone"]{ border-radius:18px !important; background:var(--vs-card) !important; border:1px dashed var(--vs-moss) !important; }
.stSlider [data-baseweb="slider"] div[role="slider"]{ background:var(--vs-sage) !important; }

/* tabs: pill bars shaped like the sidebar's active item */
[role="tablist"], .stTabs [data-baseweb="tab-list"]{ gap:6px !important; background:var(--vs-ivory) !important; border-radius:999px !important; padding:6px !important; width:fit-content; max-width:100%; overflow-x:auto; border:none !important; box-shadow:none !important; }
[role="tablist"] [role="tab"], .stTabs [data-baseweb="tab"]{ border-radius:999px !important; padding:9px 22px !important; height:auto !important; min-height:0 !important; margin:0 !important; background:transparent !important; color:var(--vs-muted) !important; font-weight:500 !important; transition:background .15s, color .15s, transform .12s; }
[role="tablist"] [role="tab"] p, [role="tablist"] [role="tab"] div{ color:inherit !important; margin:0 !important; font-size:.95rem !important; }
[role="tablist"] [role="tab"]:hover:not([aria-selected="true"]){ background:var(--vs-mist) !important; color:var(--vs-text) !important; transform:translateY(-1px); }
[role="tablist"] [role="tab"][aria-selected="true"], .stTabs [aria-selected="true"]{ background:var(--vs-sage) !important; color:#fff !important; box-shadow:0 4px 12px rgba(95,116,100,.28); }
[role="tablist"]::after, [role="tablist"]::before{ content:none !important; display:none !important; }
[role="tablist"] .react-aria-SelectionIndicator, .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{ display:none !important; }
div[data-testid="stTabs"] > div:first-child, div[data-testid="stTabs"] [role="tablist"] + div[aria-hidden]{ border-bottom:none !important; }

/* expanders */
div[data-testid="stExpander"]{ border-radius:18px !important; border:1px solid var(--vs-line) !important; background:var(--vs-card) !important; box-shadow:none !important; }

/* sidebar */
section[data-testid="stSidebar"]{ background:#F3ECE4 !important; border-right:1px solid var(--vs-line); }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a{ border-radius:14px; margin:2px 6px; padding:.35rem .7rem; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"]{ background:var(--vs-sage) !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] span{ color:#fff !important; }
div[data-testid="stAlert"]{ border-radius:18px !important; border:none !important; background:#E9EDE6 !important; color:var(--vs-text) !important; }
div[data-testid="stDataFrame"]{ border-radius:18px; overflow:hidden; }
.stPlotlyChart{ border-radius:18px; overflow:hidden; }

/* custom components */
.vs-hero{ text-align:center; padding:.6rem 0 1.6rem; }
.vs-hero h1{ margin:0; font-size:2.2rem !important; letter-spacing:.06em; }
.vs-hero .vs-sub{ margin-top:.5rem; letter-spacing:.32em; font-size:.72rem; color:var(--vs-muted); text-transform:uppercase; }
.vs-label{ font-size:1.4rem; letter-spacing:.08em; text-transform:uppercase; color:var(--vs-text); font-weight:600; margin:2.2rem 0 1rem; line-height:1.25; }
.vs-label b{ color:var(--vs-sage); font-weight:700; margin-right:.6rem; }
.vs-grid{ display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:16px; align-items:stretch; }
.vs-mcard{ background:var(--vs-card); border-radius:22px; box-shadow:var(--vs-shadow); border:1px solid rgba(255,255,255,.85);
  padding:18px 20px 18px; display:flex; flex-direction:column; gap:6px; min-height:230px; min-width:0; transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease; }
.vs-mcard:hover{ transform:translateY(-3px); box-shadow:0 16px 36px rgba(95,116,100,.18), 0 1px 0 rgba(255,255,255,.9) inset; border-color:var(--vs-moss); }
.vs-mcard.empty{ min-height:0; opacity:.85; }
.vs-mcard.empty .vs-mname{ min-height:0; }
.vs-mcode{ font-size:.7rem; letter-spacing:.16em; text-transform:uppercase; color:var(--vs-muted); font-weight:500; }
.vs-mname{ font-size:.95rem; color:var(--vs-text); line-height:1.3; font-weight:500; overflow-wrap:anywhere; min-height:2.6em; }
.vs-mvalue{ font-size:1.9rem; font-weight:400; letter-spacing:-.02em; color:var(--vs-text); font-variant-numeric:tabular-nums; line-height:1.15; overflow-wrap:anywhere; }
.vs-mvalue.long{ font-size:1.05rem; line-height:1.4; letter-spacing:0; }
.vs-munit{ font-size:.8rem; color:var(--vs-muted); line-height:1.35; overflow-wrap:anywhere; }
.vs-mcard > .vs-munit:first-of-type{ min-height:2.7em; }
.vs-mfoot{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-top:6px; min-height:38px; }
.vs-mcard details{ margin-top:auto; padding-top:10px; }
.vs-mcard summary{ cursor:pointer; list-style:none; display:inline-block; font-size:.92rem; font-weight:600; color:var(--vs-sage-dark); background:#E8EFE5; border:1.5px solid var(--vs-sage); border-radius:999px; padding:7px 18px; letter-spacing:.01em; transition:background .15s, color .15s, transform .12s; user-select:none; }
.vs-mcard summary::-webkit-details-marker{ display:none; }
.vs-mcard summary::after{ content:"  +"; font-weight:700; }
.vs-mcard details[open] summary::after{ content:"  −"; }
.vs-mcard summary:hover{ background:var(--vs-sage); color:#fff; transform:translateY(-1px); }
.vs-mcard details[open] summary{ background:var(--vs-sage); color:#fff; }
.vs-formula{ margin-top:12px; background:var(--vs-ivory); border-radius:16px; padding:14px 16px; overflow-x:auto; font-size:.9rem; line-height:1.5; color:var(--vs-sage-dark); }
.vs-formula img.vs-math{ display:block; max-width:100%; height:auto; }
.vs-formula-fallback{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.85rem; }
.vs-pill{ display:inline-block; padding:5px 16px; border-radius:999px; font-size:.95rem; font-weight:600; background:#CFE0CC; color:#27432F; border:1.5px solid var(--vs-sage); white-space:nowrap; line-height:1.3; transition:transform .12s; }
.vs-pill:hover{ transform:translateY(-1px); }
.vs-pill.sand{ background:#EBDCC4; color:#6B5438; }
.vs-pill.amber{ background:#F1D9A6; color:#6E4F14; }
.vs-pill.rose{ background:#EFC4BD; color:#7A332D; }
.vs-pill.blue{ background:#CADBE3; color:#34505E; }
.vs-kpis{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:16px; align-items:stretch; }
.vs-kpi{ background:var(--vs-card); border-radius:22px; box-shadow:var(--vs-shadow); border:1px solid rgba(255,255,255,.85); padding:18px 20px; min-width:0; display:flex; flex-direction:column; gap:6px; transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease; }
.vs-kpi:hover{ transform:translateY(-3px); box-shadow:0 16px 36px rgba(95,116,100,.18), 0 1px 0 rgba(255,255,255,.9) inset; border-color:var(--vs-moss); }
.vs-kpi .k{ font-size:.7rem; letter-spacing:.16em; text-transform:uppercase; color:var(--vs-muted); font-weight:500; }
.vs-kpi .n{ font-size:.95rem; color:var(--vs-text); font-weight:500; line-height:1.3; }
.vs-kpi .v{ font-size:1.9rem; letter-spacing:-.02em; margin-top:2px; overflow-wrap:anywhere; font-variant-numeric:tabular-nums; line-height:1.15; }
.vs-kpi .v.long{ font-size:1.15rem; line-height:1.35; letter-spacing:0; }
.vs-kpi .h{ font-size:.8rem; color:var(--vs-muted); line-height:1.35; }
.vs-kpi .p{ margin-top:6px; }
.vs-note{ display:flex; gap:14px; align-items:flex-start; background:#E9EDE6; border-radius:18px; padding:14px 18px; margin:.4rem 0 1rem; }
.vs-note .dot{ flex:0 0 28px; height:28px; border-radius:50%; background:var(--vs-sage); color:#fff; display:flex; align-items:center; justify-content:center; font-size:.8rem; font-weight:600; }
.vs-note.amber{ background:#F4EBDA; } .vs-note.amber .dot{ background:#A9803F; }
.vs-note.rose{ background:#F4E2DF; } .vs-note.rose .dot{ background:#A35D56; }
.vs-note .t{ font-weight:500; font-size:.92rem; } .vs-note .b{ font-size:.82rem; color:var(--vs-muted); line-height:1.5; }
.vs-gauge{ background:var(--vs-card); border-radius:22px; box-shadow:var(--vs-shadow); border:1px solid rgba(255,255,255,.85); padding:18px 22px; margin-bottom:14px; }
.vs-gauge .row{ display:flex; justify-content:space-between; align-items:baseline; gap:12px; flex-wrap:wrap; }
.vs-gauge .nm{ font-weight:500; font-size:.95rem; } .vs-gauge .val{ font-size:1.35rem; letter-spacing:-.01em; font-variant-numeric:tabular-nums; }
.vs-track{ position:relative; height:10px; border-radius:999px; background:#E4DDD3; margin:16px 0 8px; }
.vs-fill{ position:absolute; left:0; top:0; bottom:0; border-radius:999px; background:var(--vs-sage); }
.vs-knob{ position:absolute; top:-5px; width:20px; height:20px; border-radius:50%; background:#fff; border:5px solid var(--vs-sage); box-shadow:0 2px 6px rgba(0,0,0,.15); }
.vs-scale{ display:flex; justify-content:space-between; font-size:.7rem; color:var(--vs-muted); }
.vs-list{ margin:0; padding-left:1.1rem; } .vs-list li{ margin-bottom:.7rem; font-size:1rem; line-height:1.6; }
@media (max-width:640px){ .block-container{ padding-left:1rem; padding-right:1rem; } .vs-mvalue{ font-size:1.5rem; } }
</style>
"""

_PILL_TONES = {
    "EXCELLENT": "", "GOOD": "", "ACCEPTABLE": "blue", "MODERATE": "sand", "INFO": "blue",
    "WARNING": "amber", "CONCERNING": "amber", "CRITICAL": "rose", "SEVERE": "rose", "MISSING_DATA": "sand",
}


def tone_for(status: str) -> str:
    return _PILL_TONES.get(str(status).upper(), "sand")


def setup_page(title: str, icon: str = ":material/analytics:") -> None:
    """Page config + Calm Kit CSS. Must be the first Streamlit call on a page."""
    st.set_page_config(page_title=f"{title} · Vital Stats Suite", page_icon=icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "") -> None:
    st.html(f'<div class="vs-hero"><h1>{html.escape(title)}</h1>'
            + (f'<div class="vs-sub">{html.escape(subtitle)}</div>' if subtitle else "") + "</div>")


def label(text: str, num: Optional[int] = None) -> None:
    n = f"<b>{num:02d}.</b>" if num is not None else ""
    st.html(f'<div class="vs-label">{n}{html.escape(text)}</div>')


def pill(text: str, tone: str = "") -> str:
    return f'<span class="vs-pill {tone}">{html.escape(str(text))}</span>'


def notice(title: str, body: str = "", tone: str = "") -> None:
    mark = {"": "✓", "amber": "!", "rose": "!"}.get(tone, "i")
    st.html(f'<div class="vs-note {tone}"><div class="dot">{mark}</div><div><div class="t">{html.escape(title)}</div>'
            + (f'<div class="b">{html.escape(body)}</div>' if body else "") + "</div></div>")


def kpi_row(items: Sequence[tuple]) -> None:
    """Cards for single values. items: (label, value[, hint[, (pill_text, tone)]])."""
    cells = []
    for it in items:
        k, v = it[0], str(it[1])
        h = it[2] if len(it) > 2 else ""
        pl = it[3] if len(it) > 3 and it[3] else None
        cells.append(
            f'<div class="vs-kpi"><div class="k">{html.escape(str(k))}</div>'
            f'<div class="v{" long" if len(v) > 16 else ""}">{html.escape(v)}</div>'
            + (f'<div class="h">{html.escape(str(h))}</div>' if h else "")
            + (f'<div class="p">{pill(pl[0], pl[1])}</div>' if pl else "") + "</div>")
    st.html(f'<div class="vs-kpis">{"".join(cells)}</div>')


stat_grid = kpi_row


def result_card(m: Optional[Any], placeholder_code: str = "", placeholder_name: str = "", hint: str = "Enter the inputs to see the result.") -> None:
    """One measure card for a calculator, or an empty card with a hint while inputs are incomplete."""
    if m is not None:
        st.html(f'<div class="vs-grid">{measure_card_html(m)}</div>')
    else:
        st.html(f'<div class="vs-grid"><div class="vs-mcard empty"><div class="vs-mcode">{html.escape(placeholder_code)}</div>'
                f'<div class="vs-mname">{html.escape(placeholder_name)}</div><div class="vs-mvalue">–</div>'
                f'<div class="vs-munit">{html.escape(hint)}</div></div></div>')


_NUM = re.compile(r"^([+\-−]?[\d,]*\.?\d+%?)\s*(.*)$", re.S)


def _split_value(text: str) -> tuple:
    m = _NUM.match(str(text).strip())
    return (m.group(1), m.group(2)) if m else (str(text), "")


def measure_card_html(m: Any) -> str:
    if getattr(m, "interpretation", None) is None:
        try:
            from engine.interpretation import interpret_measure
            interpret_measure(m)
        except Exception:
            pass
    interp = getattr(m, "interpretation", None) or {}
    status = str(interp.get("status", "")).upper()
    big, rest = _split_value(m.formatted_value)
    unit_txt = rest or getattr(m, "unit", "") or ""
    footer = ""
    if status:
        footer += pill(status.title(), tone_for(status))
    if interp.get("label"):
        footer += f'<span class="vs-munit">{html.escape(str(interp["label"]))}</span>'
    formula_plain = getattr(m, "formula", "")
    latex = getattr(m, "formula_latex", "")
    det = ""
    if latex or formula_plain:
        body = formula_img_html(latex, formula_plain) if latex else f'<span class="vs-formula-fallback">{html.escape(formula_plain)}</span>'
        det = f'<details><summary>Formula</summary><div class="vs-formula">{body}</div></details>'
    _sf = str(m.shortform or m.code)
    return (f'<div class="vs-mcard"><div class="vs-mcode"' + ('' if _sf.isascii() else ' style="text-transform:none"') + f'>{html.escape(_sf)}</div>'
            f'<div class="vs-mname">{html.escape(str(m.full_name or m.name))}</div>'
            f'<div class="vs-mvalue{" long" if len(big) > 14 else ""}">{html.escape(big)}</div><div class="vs-munit">{html.escape(unit_txt)}</div>'
            f'<div class="vs-mfoot">{footer}</div>{det}</div>')


def measure_grid(measures: Iterable[Any]) -> None:
    cards = "".join(measure_card_html(m) for m in measures)
    if cards:
        st.html(f'<div class="vs-grid">{cards}</div>')
    else:
        notice("Nothing to show yet", "This dataset does not contain the inputs these measures need.", "amber")


def interpretations(title: str, measures: Iterable[Any], extra: Optional[List[str]] = None) -> None:
    items = []
    for m in measures:
        line = getattr(m, "interpretation_line", "") or ""
        if not line:
            continue
        head, sep, body = line.partition(" : ")
        items.append(f"<li><b>{html.escape(head)}</b>{' : ' + html.escape(body) if sep else ''}</li>")
    items += [f"<li>{html.escape(t)}</li>" for t in (extra or [])]
    if items:
        with st.container(border=True):
            st.html(f'<div class="vs-label" style="margin-top:.4rem">{html.escape(title)}</div><ul class="vs-list">{"".join(items)}</ul>')


def show_plot(fig: Any, key: Optional[str] = None) -> None:
    try:
        st.plotly_chart(fig, width="stretch", key=key)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, key=key)


def show_df(df: Any, **kwargs: Any) -> None:
    try:
        st.dataframe(df, width="stretch", **kwargs)
    except TypeError:
        st.dataframe(df, use_container_width=True, **kwargs)


def section_export(section_name: str, measures: List[Any], dataset_name: str, year: Optional[int], file_stub: str) -> None:
    """Single-section HTML and PDF download buttons."""
    from reports.html_export import generate_section_html_report
    from reports.pdf_export import generate_section_pdf_report
    label("Export this section")
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", dataset_name)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Download HTML report", data=generate_section_html_report(section_name, measures, dataset_name, year),
                           file_name=f"{file_stub}_{safe}.html", mime="text/html", key=f"{file_stub}_html")
    with c2:
        st.download_button("Download PDF report", data=generate_section_pdf_report(section_name, measures, dataset_name, year),
                           file_name=f"{file_stub}_{safe}.pdf", mime="application/pdf", key=f"{file_stub}_pdf")


def quality_grid(items: Sequence[tuple]) -> None:
    """items: (title, QualityCheckResult | None, unavailable_hint). Text stays inside equal-height cards."""
    cards = []
    for title, chk, hint in items:
        if chk is None or chk.score is None:
            body = (f'<div class="vs-mcode">{html.escape(title)}</div><div class="vs-mvalue">Not available</div>'
                    f'<div class="vs-munit">{html.escape(hint)}</div>')
        else:
            body = (f'<div class="vs-mcode">{html.escape(title)}</div><div class="vs-mvalue">{chk.score:.2f}</div>'
                    f'<div class="vs-mfoot">{pill(str(chk.status).title(), tone_for(chk.status))}</div>'
                    f'<div class="vs-munit">{html.escape(chk.interpretation)}</div>'
                    f'<details><summary>What to do</summary><div class="vs-formula" style="font-family:inherit;font-size:.92rem">{html.escape(chk.recommendation)}</div></details>')
        cards.append(f'<div class="vs-mcard" style="min-height:200px">{body}</div>')
    st.html(f'<div class="vs-grid">{"".join(cards)}</div>')
