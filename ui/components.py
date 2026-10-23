"""
UI Visualization Components & Editorial Design System
Implements:
1. Interactive Population Pyramid (Single dataset & Comparative overlays, Percent / Counts)
2. Broad Age Composition Breakdown (Donut chart & Dependency indicator)
3. Data Quality Myers Terminal Digit Preference Visualizer
4. Fertility (ASFR) & Mortality (ASDR) Age Schedules
5. Long-Term Trajectory & Dividend Horizon Time-Series Chart
6. Calm Bell-Curve / Range Indicator Gauges (Clean, rounded card design with zero raw HTML leaks)
"""

from __future__ import annotations
import html
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st


PALETTE = {
    "bg": "rgba(0,0,0,0)",
    "card": "#F7F2EB",
    "border": "#E8E0D6",
    "text": "#2B2E2A",
    "text_muted": "#6E726C",
    "text_light": "#8A8E88",
    "male": "#5F7464",          # Sage
    "female": "#C2A88E",        # Warm sand
    "compare_male": "#6F8794",  # Slate
    "compare_female": "#A9B7A6",# Moss
    "teal": "#7E9C8A",
    "normal_band": "rgba(95, 116, 100, 0.10)",
    "alert": "#A35D56",
    "success": "#5F7464",
}
FONT = "Inter, system-ui, sans-serif"


def create_population_pyramid(
    df_single_or_5yr: pd.DataFrame,
    title: str = "Population Pyramid by Age & Sex",
    df_compare: Optional[pd.DataFrame] = None,
    compare_label: Optional[str] = None,
    current_label: str = "Current",
    as_percentage: bool = True,
) -> go.Figure:
    """
    Creates an interactive population pyramid with rounded bars,
    crisp high-contrast colors, and optional comparison overlay.
    """
    df = df_single_or_5yr.copy()
    age_col = "age_group" if "age_group" in df.columns else ("age" if "age" in df.columns else df.columns[0])

    if "male" not in df.columns or "female" not in df.columns:
        fig = go.Figure()
        fig.update_layout(
            title=dict(text="Age distribution table requires 'male' and 'female' columns.", font=dict(family="Inter, sans-serif", size=14)),
            paper_bgcolor=PALETTE["bg"],
            plot_bgcolor=PALETTE["card"],
        )
        return fig

    males = df["male"].values.astype(float)
    females = df["female"].values.astype(float)
    ages = df[age_col].astype(str).values

    total_pop = males.sum() + females.sum()
    if total_pop <= 0:
        total_pop = 1.0

    if as_percentage:
        m_vals = (males / total_pop) * 100.0
        f_vals = (females / total_pop) * 100.0
        x_unit = "%"
        x_title = "Share of Total Population (%)"
    else:
        m_vals = males
        f_vals = females
        x_unit = ""
        x_title = "Population Count"

    fig = go.Figure()

    # Male Bars (Negative x for left side)
    fig.add_trace(go.Bar(
        y=ages,
        x=-m_vals,
        name=f"Males ({current_label})",
        orientation="h",
        marker=dict(
            color=PALETTE["male"],
            line=dict(color="#4B5E52", width=0.5),
        ),
        customdata=np.stack((males, (males / total_pop) * 100.0), axis=-1),
        hovertemplate="<b>Age %{y} — Male</b><br>Count: %{customdata[0]:,.0f}<br>Share: %{customdata[1]:.2f}%<extra></extra>",
    ))

    # Female Bars (Positive x for right side)
    fig.add_trace(go.Bar(
        y=ages,
        x=f_vals,
        name=f"Females ({current_label})",
        orientation="h",
        marker=dict(
            color=PALETTE["female"],
            line=dict(color="#A88C70", width=0.5),
        ),
        customdata=np.stack((females, (females / total_pop) * 100.0), axis=-1),
        hovertemplate="<b>Age %{y} — Female</b><br>Count: %{customdata[0]:,.0f}<br>Share: %{customdata[1]:.2f}%<extra></extra>",
    ))

    # Optional Comparison Overlay
    if df_compare is not None and not df_compare.empty:
        c_df = df_compare.copy()
        c_age_col = "age_group" if "age_group" in c_df.columns else ("age" if "age" in c_df.columns else c_df.columns[0])
        if "male" in c_df.columns and "female" in c_df.columns:
            c_males = c_df["male"].values.astype(float)
            c_females = c_df["female"].values.astype(float)
            c_tot = c_males.sum() + c_females.sum()
            if c_tot <= 0:
                c_tot = 1.0

            if as_percentage:
                c_m_vals = (c_males / c_tot) * 100.0
                c_f_vals = (c_females / c_tot) * 100.0
            else:
                c_m_vals = c_males
                c_f_vals = c_females

            c_lbl = compare_label or "Comparison"

            fig.add_trace(go.Scatter(
                y=c_df[c_age_col].astype(str).values,
                x=-c_m_vals,
                mode="lines+markers",
                name=f"Males ({c_lbl})",
                line=dict(color=PALETTE["compare_male"], width=2.2, dash="dash"),
                marker=dict(size=5, color=PALETTE["compare_male"], symbol="circle"),
                customdata=np.stack((c_males, (c_males / c_tot) * 100.0), axis=-1),
                hovertemplate=f"<b>Age %{{y}} — Male ({c_lbl})</b><br>Count: %{{customdata[0]:,.0f}}<br>Share: %{{customdata[1]:.2f}}%<extra></extra>",
            ))

            fig.add_trace(go.Scatter(
                y=c_df[c_age_col].astype(str).values,
                x=c_f_vals,
                mode="lines+markers",
                name=f"Females ({c_lbl})",
                line=dict(color=PALETTE["compare_female"], width=2.2, dash="dash"),
                marker=dict(size=5, color=PALETTE["compare_female"], symbol="circle"),
                customdata=np.stack((c_females, (c_females / c_tot) * 100.0), axis=-1),
                hovertemplate=f"<b>Age %{{y}} — Female ({c_lbl})</b><br>Count: %{{customdata[0]:,.0f}}<br>Share: %{{customdata[1]:.2f}}%<extra></extra>",
            ))

    max_v = max(m_vals.max(), f_vals.max()) * 1.15
    if as_percentage:
        tick_vals = [-round(max_v * 0.8, 1), -round(max_v * 0.4, 1), 0, round(max_v * 0.4, 1), round(max_v * 0.8, 1)]
        tick_text = [f"{abs(v):.1f}%" for v in tick_vals]
    else:
        tick_vals = [-round(max_v * 0.8), -round(max_v * 0.4), 0, round(max_v * 0.4), round(max_v * 0.8)]
        tick_text = [f"{abs(v):,.0f}" for v in tick_vals]

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family="Inter, system-ui, sans-serif", size=17, color=PALETTE["text"]),
            x=0.01,
            y=0.97,
        ),
        barmode="relative",
        bargap=0.12,
        plot_bgcolor=PALETTE["card"],
        paper_bgcolor=PALETTE["bg"],
        font=dict(family="Inter, system-ui, sans-serif", color=PALETTE["text"], size=12),
        xaxis=dict(
            title=dict(text=x_title, font=dict(size=11, color=PALETTE["text_muted"])),
            tickmode="array",
            tickvals=tick_vals,
            ticktext=tick_text,
            range=[-max_v, max_v],
            gridcolor=PALETTE["border"],
            zeroline=True,
            zerolinecolor=PALETTE["text_muted"],
            zerolinewidth=1.2,
        ),
        yaxis=dict(
            title=dict(text="Age Group", font=dict(size=11, color=PALETTE["text_muted"])),
            gridcolor=PALETTE["border"],
        ),
        legend=dict(orientation="h", yanchor="top", y=-0.14, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=40, r=40, t=60, b=70),
        height=540,
    )
    return fig


def create_age_composition_donut(
    pop_0_14: float,
    pop_15_64: float,
    pop_65_plus: float,
    title: str = "Broad Age Composition & Dependency Base",
) -> go.Figure:
    """
    Creates a donut chart showing the three demographic functional age segments:
    Youth (0-14), Working-Age (15-64), and Elderly (65+).
    """
    total = pop_0_14 + pop_15_64 + pop_65_plus
    if total <= 0:
        total = 1.0

    working_share = (pop_15_64 / total) * 100.0
    dep_ratio = ((pop_0_14 + pop_65_plus) / pop_15_64 * 100.0) if pop_15_64 > 0 else 0.0

    labels = ["Youth (0–14 yrs)", "Working-Age (15–64 yrs)", "Elderly (65+ yrs)"]
    values = [pop_0_14, pop_15_64, pop_65_plus]
    colors = [PALETTE["female"], PALETTE["male"], PALETTE["compare_male"]]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.62,
        marker=dict(
            colors=colors,
            line=dict(color="#FFFFFF", width=2.5),
        ),
        textinfo="percent",
        textposition="inside",
        insidetextfont=dict(color="#FFFFFF", size=12),
        hovertemplate="<b>%{label}</b><br>Population: %{value:,.0f}<br>Share: %{percent}<extra></extra>",
    )])

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family="Inter, system-ui, sans-serif", size=17, color=PALETTE["text"]),
            x=0.02,
            y=0.97,
        ),
        annotations=[
            dict(
                text=f"<b>{working_share:.1f}%</b><br><span style='font-size:11px; color:#6E726C;'>Working-Age</span><br><span style='font-size:10px; color:#8A8E88;'>TDR: {dep_ratio:.1f}</span>",
                x=0.5,
                y=0.5,
                font=dict(family="Inter, sans-serif", size=17, color=PALETTE["text"]),
                showarrow=False,
            )
        ],
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.03, xanchor="center", x=0.5),
        plot_bgcolor=PALETTE["card"],
        paper_bgcolor=PALETTE["bg"],
        font=dict(family="Inter, system-ui, sans-serif", color=PALETTE["text"]),
        margin=dict(l=30, r=30, t=60, b=120),
        height=440,
    )
    return fig


def create_digit_preference_chart(
    single_year_df: pd.DataFrame,
    title: str = "Terminal Digit Preference Audit (Myers' 0–9 Analysis)",
) -> go.Figure:
    """
    Visualizes terminal digit attraction (heaping) across digits 0 through 9
    against the theoretical 10.0% unheaped benchmark.
    """
    df = single_year_df.copy()
    age_col = "age" if "age" in df.columns else df.columns[0]
    pop_col = "total" if "total" in df.columns else ("male" if "male" in df.columns else df.columns[1])

    # Filter ages 10 to 69 for standard Myers calculation
    df_10_69 = df[(df[age_col] >= 10) & (df[age_col] <= 69)].copy()
    df_10_69["digit"] = df_10_69[age_col] % 10
    sum1 = df_10_69.groupby("digit")[pop_col].sum().to_dict()

    df_20_69 = df[(df[age_col] >= 20) & (df[age_col] <= 69)].copy()
    df_20_69["digit"] = df_20_69[age_col] % 10
    sum2 = df_20_69.groupby("digit")[pop_col].sum().to_dict()

    blended_counts = {}
    for d in range(10):
        s1 = sum1.get(d, 0.0)
        s2 = sum2.get(d, 0.0)
        blended_counts[d] = ((d + 1) * s1) + ((9 - d) * s2)

    total_blended = sum(blended_counts.values()) or 1.0
    digits = [str(d) for d in range(10)]
    pcts = [(blended_counts[d] / total_blended) * 100.0 for d in range(10)]

    # Color code bars by deviation from 10%
    bar_colors = []
    for p in pcts:
        if p > 12.0:
            bar_colors.append(PALETTE["alert"])  # Heavy heaping
        elif p > 10.5:
            bar_colors.append(PALETTE["male"])   # Moderate heaping
        elif p < 8.5:
            bar_colors.append(PALETTE["compare_male"]) # Avoidance
        else:
            bar_colors.append(PALETTE["teal"])   # Near ideal

    fig = go.Figure()

    # Digit Bars
    fig.add_trace(go.Bar(
        x=digits,
        y=pcts,
        marker=dict(
            color=bar_colors,
            line=dict(color=PALETTE["border"], width=1),
        ),
        customdata=[p - 10.0 for p in pcts],
        hovertemplate="<b>Terminal Digit: %{x}</b><br>Blended Share: %{y:.2f}%<br>Deviation from 10%: %{customdata:+.2f}%<extra></extra>",
    ))

    # Expected 10% benchmark dashed line
    fig.add_shape(
        type="line",
        x0=-0.5,
        x1=9.5,
        y0=10.0,
        y1=10.0,
        line=dict(color="#2B2E2A", width=1.5, dash="dash"),
    )

    fig.add_annotation(
        x=9.2,
        y=10.6,
        text="Expected: 10.0%",
        showarrow=False,
        font=dict(size=10, color=PALETTE["text_muted"], family="Inter, sans-serif"),
    )

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family="Inter, system-ui, sans-serif", size=17, color=PALETTE["text"]),
            x=0.02,
            y=0.97,
        ),
        plot_bgcolor=PALETTE["card"],
        paper_bgcolor=PALETTE["bg"],
        font=dict(family="Inter, system-ui, sans-serif", color=PALETTE["text"], size=12),
        xaxis=dict(
            title=dict(text="Terminal Digit (0 to 9)", font=dict(size=11, color=PALETTE["text_muted"])),
            dtick=1,
            gridcolor=PALETTE["border"],
        ),
        yaxis=dict(
            title=dict(text="Blended Population Share (%)", font=dict(size=11, color=PALETTE["text_muted"])),
            gridcolor=PALETTE["border"],
            range=[0, max(max(pcts) * 1.25, 16)],
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        height=380,
    )
    return fig


def create_fertility_schedule_chart(
    fertility_df: pd.DataFrame,
    title: str = "Age-Specific Fertility Rates (ASFR Schedule)",
) -> go.Figure:
    """
    Renders maternal age-specific fertility rate curve across 5-year childbearing intervals.
    """
    df = fertility_df.copy()
    if "asfr" not in df.columns and "births" in df.columns and "female_pop" in df.columns:
        df["asfr"] = (df["births"] / df["female_pop"]) * 1000.0

    age_col = "age_group" if "age_group" in df.columns else df.columns[0]
    asfr_col = "asfr" if "asfr" in df.columns else df.columns[1]

    fig = go.Figure()

    # ASFR Spline Area
    fig.add_trace(go.Scatter(
        x=df[age_col],
        y=df[asfr_col],
        mode="lines+markers",
        line=dict(color=PALETTE["male"], width=3, shape="spline"),
        marker=dict(size=7, color=PALETTE["male"]),
        fill="tozeroy",
        fillcolor="rgba(95, 116, 100, 0.14)",
        name="ASFR (per 1,000)",
        hovertemplate="<b>Age Group: %{x}</b><br>ASFR: %{y:.1f} births / 1,000 women<extra></extra>",
    ))

    # Highlight peak fertility
    max_idx = df[asfr_col].idxmax()
    peak_age = df.loc[max_idx, age_col]
    peak_val = df.loc[max_idx, asfr_col]

    fig.add_annotation(
        x=peak_age,
        y=peak_val,
        text=f"<b>Peak: {peak_val:.1f}</b>",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowcolor=PALETTE["male"],
        font=dict(family="Inter, sans-serif", size=11, color=PALETTE["text"]),
        yshift=10,
    )

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family="Inter, system-ui, sans-serif", size=17, color=PALETTE["text"]),
            x=0.02,
            y=0.97,
        ),
        plot_bgcolor=PALETTE["card"],
        paper_bgcolor=PALETTE["bg"],
        font=dict(family="Inter, system-ui, sans-serif", color=PALETTE["text"], size=12),
        xaxis=dict(
            title=dict(text="Maternal Age Group (Years)", font=dict(size=11, color=PALETTE["text_muted"])),
            gridcolor=PALETTE["border"],
        ),
        yaxis=dict(
            title=dict(text="Births per 1,000 Women", font=dict(size=11, color=PALETTE["text_muted"])),
            gridcolor=PALETTE["border"],
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        height=380,
    )
    return fig


def create_mortality_schedule_chart(
    mortality_df: pd.DataFrame,
    title: str = "Age-Specific Death Rate (ASDR Schedule)",
    log_scale: bool = False,
) -> go.Figure:
    """
    Renders demographic mortality curve across age groups (J-shaped / U-shaped curve).
    """
    df = mortality_df.copy()
    if "asdr" not in df.columns and "deaths" in df.columns and "population" in df.columns:
        df["asdr"] = (df["deaths"] / df["population"]) * 1000.0

    age_col = "age_group" if "age_group" in df.columns else df.columns[0]
    asdr_col = "asdr" if "asdr" in df.columns else df.columns[1]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df[age_col],
        y=df[asdr_col],
        mode="lines+markers",
        line=dict(color=PALETTE["compare_male"], width=2.8, shape="spline"),
        marker=dict(size=6, color=PALETTE["compare_male"]),
        fill="tozeroy",
        fillcolor="rgba(111, 135, 148, 0.12)",
        name="ASDR (per 1,000)",
        hovertemplate="<b>Age Group: %{x}</b><br>Death Rate: %{y:.2f} per 1,000<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family="Inter, system-ui, sans-serif", size=17, color=PALETTE["text"]),
            x=0.02,
            y=0.97,
        ),
        plot_bgcolor=PALETTE["card"],
        paper_bgcolor=PALETTE["bg"],
        font=dict(family="Inter, system-ui, sans-serif", color=PALETTE["text"], size=12),
        xaxis=dict(
            title=dict(text="Age Group", font=dict(size=11, color=PALETTE["text_muted"])),
            gridcolor=PALETTE["border"],
        ),
        yaxis=dict(
            title=dict(text="Deaths per 1,000 Population" + (" (Log Scale)" if log_scale else ""), font=dict(size=11, color=PALETTE["text_muted"])),
            gridcolor=PALETTE["border"],
            type="log" if log_scale else "linear",
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        height=380,
    )
    return fig


def create_trajectory_chart(
    combined_df: pd.DataFrame,
    dividend_start_year: Optional[int] = None,
    dividend_end_year: Optional[int] = None,
    title: str = "Long-Term Demographic Trajectory & Transition Horizon",
) -> go.Figure:
    """
    Creates an editorial time-series chart showing historical series (1970-2024)
    and future projections (2025-2054) with dividend window highlight.
    """
    df = combined_df.copy()
    for new, alts in {"tfr": ["TFR"], "pct_working_15_64": ["pct_working_age"], "pct_elderly_65_plus": ["pct_elderly"]}.items():
        if new not in df.columns:
            for a in alts:
                if a in df.columns:
                    df[new] = df[a]
    fig = go.Figure()

    df_hist = df[~df["is_projected"].astype(bool)]
    df_proj = df[df["is_projected"].astype(bool)]

    # Working Age Share %
    fig.add_trace(go.Scatter(
        x=df_hist["year"],
        y=df_hist["pct_working_15_64"],
        name="Working-Age (15–64) [Hist]",
        line=dict(color=PALETTE["male"], width=2.8),
        mode="lines",
        hovertemplate="<b>%{x} (Hist)</b><br>Working-Age Share: %{y:.1f}%<extra></extra>",
    ))
    if not df_proj.empty:
        fig.add_trace(go.Scatter(
            x=df_proj["year"],
            y=df_proj["pct_working_15_64"],
            name="Working-Age (Projected)",
            line=dict(color=PALETTE["male"], width=2.8, dash="dash"),
            mode="lines",
            hovertemplate="<b>%{x} (Proj)</b><br>Working-Age Share: %{y:.1f}%<extra></extra>",
        ))

    # Elderly Share %
    fig.add_trace(go.Scatter(
        x=df_hist["year"],
        y=df_hist["pct_elderly_65_plus"],
        name="Elderly (65+) [Hist]",
        line=dict(color=PALETTE["compare_male"], width=2.2),
        mode="lines",
        hovertemplate="<b>%{x} (Hist)</b><br>Elderly Share: %{y:.1f}%<extra></extra>",
    ))
    if not df_proj.empty:
        fig.add_trace(go.Scatter(
            x=df_proj["year"],
            y=df_proj["pct_elderly_65_plus"],
            name="Elderly (Projected)",
            line=dict(color=PALETTE["compare_male"], width=2.2, dash="dash"),
            mode="lines",
            hovertemplate="<b>%{x} (Proj)</b><br>Elderly Share: %{y:.1f}%<extra></extra>",
        ))

    # TFR Line (Secondary Axis)
    fig.add_trace(go.Scatter(
        x=df_hist["year"],
        y=df_hist["tfr"],
        name="TFR (Children / Woman) [Hist]",
        line=dict(color=PALETTE["teal"], width=2),
        yaxis="y2",
        mode="lines",
        hovertemplate="<b>%{x} (Hist)</b><br>TFR: %{y:.2f}<extra></extra>",
    ))
    if not df_proj.empty:
        fig.add_trace(go.Scatter(
            x=df_proj["year"],
            y=df_proj["tfr"],
            name="TFR (Projected)",
            line=dict(color=PALETTE["teal"], width=2, dash="dash"),
            yaxis="y2",
            mode="lines",
            hovertemplate="<b>%{x} (Proj)</b><br>TFR: %{y:.2f}<extra></extra>",
        ))

    # Highlight Demographic Dividend Window (Working Age >= 60%)
    if dividend_start_year and dividend_end_year:
        fig.add_vrect(
            x0=dividend_start_year,
            x1=dividend_end_year,
            fillcolor=PALETTE["normal_band"],
            layer="below",
            line_width=0,
            annotation_text=f"Demographic Dividend Window ({dividend_start_year}–{dividend_end_year})",
            annotation_position="top left",
            annotation=dict(font_size=11, font_color=PALETTE["male"], font_family="Inter, sans-serif"),
        )

    # Present Transition Line
    if not df_hist.empty:
        trans_year = int(df_hist["year"].max())
        fig.add_vline(
            x=trans_year,
            line=dict(color=PALETTE["text_muted"], width=1, dash="dot"),
            annotation_text="Present Transition",
            annotation_position="bottom right",
            annotation=dict(font_size=10, font_color=PALETTE["text_muted"], font_family="Inter, sans-serif"),
        )

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family="Inter, system-ui, sans-serif", size=17, color=PALETTE["text"]),
            x=0.02,
            y=0.97,
        ),
        plot_bgcolor=PALETTE["card"],
        paper_bgcolor=PALETTE["bg"],
        font=dict(family="Inter, system-ui, sans-serif", color=PALETTE["text"], size=12),
        xaxis=dict(
            title=dict(text="Year", font=dict(size=11, color=PALETTE["text_muted"])),
            gridcolor=PALETTE["border"],
        ),
        yaxis=dict(
            title=dict(text="Population Share (%)", font=dict(size=11, color=PALETTE["text_muted"])),
            gridcolor=PALETTE["border"],
            range=[0, 80],
        ),
        yaxis2=dict(
            title=dict(text="Total Fertility Rate (TFR)", font=dict(size=11, color=PALETTE["teal"])),
            overlaying="y",
            side="right",
            range=[0, 6.5],
            gridcolor="rgba(0,0,0,0)",
        ),
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=40, r=40, t=60, b=110),
        height=520,
    )
    return fig


def render_calm_gauge_html(
    measure_name: str, value: float, formatted_value: str, unit: str, status: str, status_label: str,
    gauge_min: float, gauge_max: float, source: str, is_heuristic: bool = False,
) -> str:
    """Calm range indicator: a pill track with a marker, styled by the Calm Kit theme (see ui.theme.CSS)."""
    span = gauge_max - gauge_min
    pct = ((max(gauge_min, min(gauge_max, value)) - gauge_min) / span * 100.0) if span > 0 else 50.0
    tone = {"EXCELLENT": "", "GOOD": "", "MODERATE": "sand", "WARNING": "amber", "CONCERNING": "amber",
            "CRITICAL": "rose", "SEVERE": "rose"}.get(str(status).upper(), "sand")
    knob = {"": "#5F7464", "sand": "#A88C70", "amber": "#A9803F", "rose": "#A35D56"}[tone]
    tag = "Heuristic band" if is_heuristic else source
    return (
        f'<div class="vs-gauge"><div class="row"><div><span class="nm">{html.escape(measure_name)}</span> '
        f'<span class="vs-munit">{html.escape(tag)}</span></div><div class="val">{html.escape(formatted_value)}</div></div>'
        f'<div class="vs-track"><div class="vs-fill" style="width:{pct:.1f}%;background:{knob}"></div>'
        f'<div class="vs-knob" style="left:calc({pct:.1f}% - 10px);border-color:{knob}"></div></div>'
        f'<div class="vs-scale"><span>{gauge_min:g}</span><span>{html.escape(unit)}</span><span>{gauge_max:g}</span></div>'
        f'<div style="margin-top:8px"><span class="vs-pill {tone}">{html.escape(str(status).title())}</span> '
        f'<span class="vs-munit">{html.escape(status_label)}</span></div></div>'
    )


def render_calm_gauge(
    measure_name: str, value: float, formatted_value: str, unit: str, status: str, status_label: str,
    gauge_min: float, gauge_max: float, source: str, is_heuristic: bool = False,
):
    """Render a calm gauge in Streamlit."""
    st.html(render_calm_gauge_html(measure_name, value, formatted_value, unit, status, status_label,
                                   gauge_min, gauge_max, source, is_heuristic))


def create_life_table_curves(
    life_table_df: pd.DataFrame,
    title: str = "Abridged Life Table: Survivorship (lx) & Remaining Life Expectancy (ex)",
) -> go.Figure:
    """Creates a dual-axis interactive demographic life table survivorship curve."""
    df = life_table_df.copy()
    fig = go.Figure()
    
    x_vals = df["x"] if "x" in df.columns else (df["age"] if "age" in df.columns else df.index)
    
    # 1. lx Survivorship Curve
    if "lx" in df.columns:
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=df["lx"],
            name="Survivors (lx)",
            line=dict(color=PALETTE["male"], width=2.8),
            mode="lines+markers",
            marker=dict(size=5, color=PALETTE["male"]),
            fill="tozeroy",
            fillcolor="rgba(95, 116, 100, 0.08)",
            hovertemplate="<b>Age %{x}</b><br>Survivors lx: %{y:,.0f} per 100,000<extra></extra>",
            yaxis="y1",
        ))
        
    # 2. ex Life Expectancy Curve (Secondary Axis)
    if "ex" in df.columns:
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=df["ex"],
            name="Life Expectancy (ex)",
            line=dict(color=PALETTE["compare_male"], width=2.4, dash="dot"),
            mode="lines+markers",
            marker=dict(size=5, color=PALETTE["compare_male"]),
            hovertemplate="<b>Age %{x}</b><br>Remaining Life Expectancy ex: %{y:.1f} years<extra></extra>",
            yaxis="y2",
        ))
        
    fig.update_layout(
        title=dict(text=title, font=dict(family="Inter, system-ui, sans-serif", size=17, color=PALETTE["text"])),
        paper_bgcolor=PALETTE["bg"],
        plot_bgcolor=PALETTE["card"],
        font=dict(family="Inter, system-ui, sans-serif", color=PALETTE["text"], size=12),
        xaxis=dict(
            title=dict(text="Exact Age (x)", font=dict(size=11, color=PALETTE["text_muted"])),
            gridcolor=PALETTE["border"],
        ),
        yaxis=dict(
            title=dict(text="Survivors (lx per 100,000 radix)", font=dict(size=11, color=PALETTE["male"])),
            gridcolor=PALETTE["border"],
            range=[0, 105000],
        ),
        yaxis2=dict(
            title=dict(text="Life Expectancy (ex in years)", font=dict(size=11, color=PALETTE["compare_male"])),
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=45, r=45, t=60, b=90),
        height=420,
    )
    return fig


def create_sprague_graduation_chart(
    five_year_counts: List[float],
    graduated_single_df: pd.DataFrame,
    start_age: int = 0,
    title: str = "Sprague Osculatory Graduation: 5-Year Cohorts vs Graduated Single-Year Age Distribution",
) -> go.Figure:
    """Visualizes the Sprague interpolation comparison with exact 5-year group area conservation."""
    fig = go.Figure()
    
    # 1. Step representation of 5-year groups (averaged per single year)
    step_ages = []
    step_vals = []
    for i, w in enumerate(five_year_counts):
        base_a = start_age + i * 5
        for a in range(base_a, base_a + 5):
            step_ages.append(a)
            step_vals.append(w / 5.0)
            
    fig.add_trace(go.Bar(
        x=step_ages,
        y=step_vals,
        name="Reported 5-Year Group (Density / Year)",
        marker=dict(color="rgba(194, 168, 142, 0.45)", line=dict(color=PALETTE["female"], width=0.5)),
        hovertemplate="<b>Age %{x}</b><br>5-Yr Group Annualized Density: %{y:,.0f}<extra></extra>",
    ))
    
    # 2. Graduated Single-Year Smooth Curve
    fig.add_trace(go.Scatter(
        x=graduated_single_df["age"],
        y=graduated_single_df["graduated_population"],
        name="Sprague Graduated Single-Year Curve",
        line=dict(color=PALETTE["male"], width=2.8),
        mode="lines",
        hovertemplate="<b>Age %{x}</b><br>Graduated Single-Year Pop: %{y:,.0f}<extra></extra>",
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(family="Inter, system-ui, sans-serif", size=17, color=PALETTE["text"])),
        paper_bgcolor=PALETTE["bg"],
        plot_bgcolor=PALETTE["card"],
        font=dict(family="Inter, system-ui, sans-serif", color=PALETTE["text"], size=12),
        xaxis=dict(
            title=dict(text="Single-Year Age", font=dict(size=11, color=PALETTE["text_muted"])),
            gridcolor=PALETTE["border"],
        ),
        yaxis=dict(
            title=dict(text="Single-Year Population Count", font=dict(size=11, color=PALETTE["text_muted"])),
            gridcolor=PALETTE["border"],
        ),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=45, r=45, t=60, b=90),
        height=420,
    )
    return fig

