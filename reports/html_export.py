"""
Standalone HTML Dashboard Export Engine (Fix B17)
Generates self-contained, offline-compatible HTML dashboard reports
strictly formatted to an editorial warm cream, terracotta, and crisp typographic design system.
Completely standalone without Streamlit or external runtime dependencies.
"""

from __future__ import annotations
import html
from typing import Dict, Any, Optional, List
from engine.pipeline import DemographicPipelineResult
from engine.formulas import formula_img_html


def render_standalone_gauge_html(
    measure_name: str,
    value: float,
    formatted_value: str,
    unit: str,
    status: str,
    status_label: str,
    gauge_min: float,
    gauge_max: float,
    source: str = "Demographic Standard",
    is_heuristic: bool = False,
) -> str:
    """Renders a self-contained SVG/HTML horizontal indicator bar for standalone HTML exports."""
    clamped_val = max(gauge_min, min(gauge_max, value))
    pct = ((clamped_val - gauge_min) / (gauge_max - gauge_min) * 100.0) if gauge_max > gauge_min else 50.0
    
    status_upper = status.upper()
    color_map = {
        "EXCELLENT": "#5F7464",
        "GOOD": "#6F8794",
        "MODERATE": "#5F7464",
        "WARNING": "#A9803F",
        "CONCERNING": "#A9803F",
        "CRITICAL": "#A35D56",
        "SEVERE": "#A35D56",
    }
    bar_color = color_map.get(status_upper, "#5F7464")
    
    return f"""
    <div style="background: #FFFFFF; border: 1px solid #E8E0D6; border-radius: 16px; padding: 14px 18px; margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px;">
            <div>
                <span style="font-weight: 700; font-size: 15px; color: #2B2E2A;">{html.escape(measure_name)}</span>
                <span style="font-size: 11.5px; color: #7C807A; margin-left: 8px;">{html.escape(source)}</span>
            </div>
            <div style="text-align: right;">
                <span style="font-weight: 700; font-size: 16px; color: #2B2E2A;">{html.escape(formatted_value)}</span>
            </div>
        </div>
        <div style="position: relative; height: 10px; background: #EFE9DF; border-radius: 5px; overflow: hidden; margin-bottom: 6px;">
            <div style="width: {pct:.1f}%; height: 100%; background: {bar_color}; border-radius: 5px;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 11.5px; color: #7C807A;">
            <span>{gauge_min:.1f}</span>
            <span style="color: {bar_color}; font-weight: 600;">{html.escape(status_label)}</span>
            <span>{gauge_max:.1f} {html.escape(unit)}</span>
        </div>
    </div>
    """


def generate_standalone_html_dashboard(
    result: DemographicPipelineResult,
    pyramid_html_div: Optional[str] = None,
) -> str:
    """
    Constructs a standalone HTML document containing the full demographic evaluation,
    calm gauges, quality diagnostic cards, full measures tables with shortforms,
    and plain-language interpretations at the end of each section.
    """
    gauges_html = ""
    for code, m in result.measures.items():
        interp = m.interpretation or {}
        gauges_html += render_standalone_gauge_html(
            measure_name=m.name,
            value=m.raw_value,
            formatted_value=m.formatted_value,
            unit=m.unit,
            status=interp.get("status", "MODERATE"),
            status_label=interp.get("label", "Standard"),
            gauge_min=interp.get("gauge_min", 0.0),
            gauge_max=interp.get("gauge_max", 100.0),
            source=interp.get("source", "Demographic Standard"),
            is_heuristic=interp.get("is_heuristic", False),
        )
        
    concerns_html = ""
    for c in result.top_concerns:
        sev = c.get("severity", "WARNING")
        bg_col = "#F4E2DF" if sev in ("CRITICAL", "SEVERE") else "#F4EBDA"
        txt_col = "#A35D56" if sev in ("CRITICAL", "SEVERE") else "#5F7464"
        concerns_html += f"""
        <div style="background: {bg_col}; border: 1px solid rgba(95,116,100,0.25); border-radius: 16px; padding: 12px 16px; margin-bottom: 10px;">
            <div style="font-weight: 700; color: {txt_col}; font-size: 14.5px; margin-bottom: 4px;">{html.escape(c.get('title', ''))}</div>
            <div style="font-size: 13px; color: #2B2E2A; line-height: 1.4;">{html.escape(c.get('description', ''))}</div>
            <div style="font-size: 12px; color: #7C807A; margin-top: 4px; font-style: italic;">{html.escape(c.get('recommendation', ''))}</div>
        </div>
        """
        
    # Interpretations grouped by block
    interpretations_html = ""
    sections_order = [
        ("A_COMPOSITION", "Block A: Sex Composition"),
        ("B_AGE_STRUCTURE", "Block B: Age Structure & Dependency"),
        ("C_FERTILITY", "Block C: Fertility & Reproduction"),
        ("D_MORTALITY", "Block D: Mortality & Standardization"),
        ("F_NUPTIALITY", "Block F: Nuptiality & Marital Dynamics"),
        ("G_MIGRATION", "Block G: Migration & Spatial Redistribution"),
    ]
    for sec_key, sec_title in sections_order:
        entries = result.section_interpretations.get(sec_key, [])
        if entries:
            interpretations_html += f"""
            <div style="margin-top: 20px; border-top: 1px dashed #E8E0D6; padding-top: 12px;">
                <h3 style="font-size: 16px; color: #5F7464; margin-bottom: 8px;">{html.escape(sec_title)} — Interpretations</h3>
                <ul style="padding-left: 20px; margin: 0; font-size: 13px; line-height: 1.6;">
            """
            for e in entries:
                interpretations_html += f"""
                    <li style="margin-bottom: 6px;">
                        <strong>{html.escape(e['line'].partition(' : ')[0])}</strong> : 
                        <span style="color: #2B2E2A;">{html.escape(e['line'].partition(' : ')[2])}</span>
                    </li>
                """
            interpretations_html += "</ul></div>"

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vital Stats Suite — {html.escape(result.dataset_name)}</title>
    <style>
        body {{
            background-color: #F8F2EC;
            color: #2B2E2A;
            font-family: Inter, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 32px 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 980px;
            margin: 0 auto;
        }}
        h1, h2, h3 {{
            font-family: Inter, sans-serif;
            font-weight: 600;
            color: #2B2E2A;
        }}
        h1 {{
            font-size: 30px;
            margin-bottom: 4px;
        }}
        .meta-bar {{
            font-size: 14px;
            color: #5F7464;
            margin-bottom: 24px;
            font-weight: 500;
        }}
        .card {{
            background: #FFFFFF;
            border: 1px solid #E8E0D6;
            border-radius: 20px;
            padding: 24px 28px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(110,90,70,0.06);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-top: 12px;
        }}
        th, td {{
            text-align: left;
            padding: 9px 12px;
            border-bottom: 1px solid #E8E0D6;
        }}
        th {{
            font-family: Inter, sans-serif;
            font-weight: 600;
            color: #2B2E2A;
            background: #F8F4EE;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 5px;
            font-size: 11px;
            font-weight: 600;
        }}
        .badge-excellent {{ background: #E7EBE4; color: #5F7464; }}
        .badge-good {{ background: #E6EBEE; color: #6F8794; }}
        .badge-moderate {{ background: #F4EBDA; color: #5F7464; }}
        .badge-warning {{ background: #F4EBDA; color: #A9803F; }}
        .badge-critical {{ background: #F4E2DF; color: #A35D56; }}
        .badge-severe {{ background: #F4E2DF; color: #A35D56; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Vital Statistics Suite</h1>
        <div class="meta-bar">Dataset: {html.escape(result.dataset_name)} &bull; Year: {result.year or 'Current'} &bull; {result.computable_count} / {result.total_measures_target} Indicators Evaluated</div>
        
        <div class="card">
            <h2>Executive Demographic Synthesis</h2>
            <p style="font-size: 14.5px; color: #2B2E2A; line-height: 1.5;">{html.escape(result.executive_summary.replace("**", ""))}</p>
            {concerns_html}
        </div>
        
        {f'<div class="card"><h2>Population Structure Pyramid</h2>{pyramid_html_div}</div>' if pyramid_html_div else ''}
        
        <div class="card">
            <h2>Demographic Indicators & Benchmark Gauges</h2>
            {gauges_html}
        </div>
        
        <div class="card">
            <h2>Data Quality & Census Coverage Audits</h2>
            <table>
                <thead>
                    <tr>
                        <th>Diagnostic Test</th>
                        <th>Score</th>
                        <th>Status</th>
                        <th>Demographic Interpretation</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'''
                    <tr>
                        <td><strong>{html.escape(q.name)}</strong></td>
                        <td>{f"{q.score:.2f}" if q.score is not None else "N/A"}</td>
                        <td><span class="badge badge-{q.status.lower()}">{html.escape(q.status)}</span></td>
                        <td>{html.escape(q.interpretation)}</td>
                    </tr>
                    ''' for q in result.quality_checks.values()])}
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>Complete Demographic Measures Inventory & Interpretations</h2>
            <table>
                <thead>
                    <tr>
                        <th>Code</th>
                        <th>Measure Name (Shortform)</th>
                        <th>Computed Value</th>
                        <th>Status</th>
                        <th>Standard Formula</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'''
                    <tr>
                        <td><strong>{html.escape(m.code)}</strong></td>
                        <td>{html.escape(m.name)}</td>
                        <td><strong>{html.escape(m.formatted_value)}</strong></td>
                        <td><span class="badge badge-{(m.interpretation.get('status','moderate')).lower()}">{html.escape(m.interpretation.get('status','Standard'))}</span></td>
                        <td>{formula_img_html(m.formula_latex, m.formula, 14.0) if m.formula_latex else html.escape(m.formula)}</td>
                    </tr>
                    ''' for m in result.measures.values()])}
                </tbody>
            </table>
            
            {interpretations_html}
        </div>
        
        <div style="text-align: center; color: #8A8E88; font-size: 12px; margin-top: 32px;">
            Vital Statistics Suite &bull; Editorial Demographic Intelligence
        </div>
    </div>
</body>
</html>
    """
    return doc


def generate_section_html_report(
    section_name: str,
    measures: List[Any],
    dataset_name: str,
    year: Optional[int] = None,
) -> str:
    """Generates a standalone single-section HTML report (R7)."""
    measures_rows = "".join([f"""
    <tr>
        <td style="padding: 10px 14px; border-bottom: 1px solid #E8E0D6;"><strong>{html.escape(m.code)}</strong></td>
        <td style="padding: 10px 14px; border-bottom: 1px solid #E8E0D6;">{html.escape(m.name)}</td>
        <td style="padding: 10px 14px; border-bottom: 1px solid #E8E0D6;"><strong>{html.escape(m.formatted_value)}</strong></td>
        <td style="padding: 10px 14px; border-bottom: 1px solid #E8E0D6;">{formula_img_html(m.formula_latex, m.formula, 14.0) if getattr(m, 'formula_latex', '') else html.escape(m.formula)}</td>
    </tr>
    """ for m in measures])
    
    interps_items = "".join([f"""
    <li style="margin-bottom: 8px;">
        <strong>{html.escape((getattr(m, 'interpretation_line', '') or m.name).partition(' : ')[0])}</strong> : <span>{html.escape((getattr(m, 'interpretation_line', '') or m.plain_interpretation or '').partition(' : ')[2])}</span>
    </li>
    """ for m in measures if m.plain_interpretation or getattr(m, 'notes', '')])
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{html.escape(section_name)} Report — {html.escape(dataset_name)}</title>
    <style>
        body {{ background-color: #F8F2EC; color: #2B2E2A; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 32px 20px; line-height: 1.6; }}
        .card {{ background: #FFFFFF; border: 1px solid #E8E0D6; border-radius: 20px; padding: 24px; margin-bottom: 24px; max-width: 900px; margin-left: auto; margin-right: auto; }}
        h1, h2, h3 {{ font-family: Inter, sans-serif; color: #2B2E2A; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
        th {{ text-align: left; padding: 10px 14px; background: #EFE9DF; border-bottom: 2px solid #E8E0D6; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>{html.escape(section_name)} Statistical Report</h1>
        <p style="color: #5F7464; font-size: 14px; font-weight: 600;">Dataset: {html.escape(dataset_name)} {f'({year})' if year else ''} &bull; Vital Statistics Suite</p>
        <hr style="border: none; border-top: 1px solid #E8E0D6; margin: 16px 0;">
        <h2>Section Measures</h2>
        <table>
            <thead>
                <tr>
                    <th>Code</th>
                    <th>Measure Name (Shortform)</th>
                    <th>Result</th>
                    <th>Formula</th>
                </tr>
            </thead>
            <tbody>
                {measures_rows}
            </tbody>
        </table>
        <div style="margin-top: 24px;">
            <h3>Demographic Interpretations</h3>
            <ul style="padding-left: 20px;">
                {interps_items}
            </ul>
        </div>
        <div style="text-align: center; color: #8A8E88; font-size: 11.5px; margin-top: 24px;">
            Vital Statistics Suite &bull; Single-Section Statistical Report
        </div>
    </div>
</body>
</html>"""

