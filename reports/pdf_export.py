"""
PDF Export Engine for Vital Stats Suite (Fix B16)
Generates:
1. Detailed Demographic Report (Complete breakdown of all measures, tables, formulas, benchmarks, and plain-language interpretations)
2. Executive Summary Brief (Key concerns, data quality, and plain-language policy findings)

Uses ReportLab with XML escaping (xml.sax.saxutils.escape) on all dynamic text.
"""

from __future__ import annotations
import io
import os
import xml.sax.saxutils as saxutils
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from engine.pipeline import DemographicPipelineResult


def _esc(val: Any) -> str:
    """Safely escapes text for ReportLab Paragraph XML parser."""
    return saxutils.escape(str(val) if val is not None else "")


CLR_BG = colors.HexColor("#F8F2EC")
CLR_TEXT = colors.HexColor("#2B2E2A")
CLR_TEXT_MUTED = colors.HexColor("#7C807A")
CLR_TERRACOTTA = colors.HexColor("#5F7464")
CLR_BORDER = colors.HexColor("#E8E0D6")
CLR_WHITE = colors.HexColor("#FFFFFF")
CLR_CRITICAL = colors.HexColor("#A35D56")
CLR_SUCCESS = colors.HexColor("#5F7464")


def generate_detailed_pdf_report(
    result: DemographicPipelineResult,
    output_path: Optional[str] = None,
) -> bytes:
    """Generates a multi-page comprehensive demographic statistical PDF report with plain interpretations."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer if output_path is None else output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=CLR_TEXT,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=CLR_TERRACOTTA,
        spaceAfter=12,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=CLR_TEXT,
        spaceBefore=14,
        spaceAfter=8,
    )
    sub_heading = ParagraphStyle(
        "SubHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=CLR_TERRACOTTA,
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=CLR_TEXT,
    )
    interp_style = ParagraphStyle(
        "InterpStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=CLR_TEXT,
    )
    muted_style = ParagraphStyle(
        "Muted",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=CLR_TEXT_MUTED,
    )
    
    story = []
    
    # 1. Header
    story.append(Paragraph(f"Vital Statistics Suite — Demographic Analysis Report", title_style))
    meta_str = f"Dataset: <b>{_esc(result.dataset_name)}</b>"
    if result.year:
        meta_str += f" | Year: <b>{_esc(result.year)}</b>"
    if result.region:
        meta_str += f" | Region: <b>{_esc(result.region)}</b>"
    meta_str += f" | Evaluated Battery: <b>{result.computable_count} / {result.total_measures_target} Measures</b>"
    story.append(Paragraph(meta_str, subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=CLR_TERRACOTTA, spaceAfter=10))
    
    # 2. Executive Synthesis
    story.append(Paragraph("1. Executive Demographic Synthesis", section_heading))
    story.append(Paragraph(_esc(result.executive_summary.replace("**", "")), body_style))
    story.append(Spacer(1, 10))
    
    # Top Concerns Callout Table
    if result.top_concerns:
        concern_rows = [
            [
                Paragraph("<b>Priority Concern</b>", ParagraphStyle("Hdr", parent=body_style, textColor=CLR_WHITE, fontName="Helvetica-Bold")),
                Paragraph("<b>Severity</b>", ParagraphStyle("Hdr", parent=body_style, textColor=CLR_WHITE, fontName="Helvetica-Bold")),
                Paragraph("<b>Interpretation & Demographic Guidance</b>", ParagraphStyle("Hdr", parent=body_style, textColor=CLR_WHITE, fontName="Helvetica-Bold")),
            ]
        ]
        for c in result.top_concerns:
            sev_bg = CLR_CRITICAL if c.get("severity") in ("CRITICAL", "SEVERE") else CLR_TERRACOTTA
            concern_rows.append([
                Paragraph(f"<b>{_esc(c.get('title', ''))}</b>", body_style),
                Paragraph(f"<b>{_esc(c.get('severity', ''))}</b>", ParagraphStyle("CSev", parent=body_style, textColor=sev_bg, fontName="Helvetica-Bold")),
                Paragraph(f"{_esc(c.get('description', ''))} {_esc(c.get('recommendation', ''))}", muted_style),
            ])
            
        t_concerns = Table(concern_rows, colWidths=[2.2 * inch, 1.0 * inch, 4.3 * inch])
        t_concerns.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), CLR_TEXT),
            ("TEXTCOLOR", (0, 0), (-1, 0), CLR_WHITE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [CLR_WHITE, colors.HexColor("#F8F4EE")]),
            ("GRID", (0, 0), (-1, -1), 0.5, CLR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t_concerns)
        story.append(Spacer(1, 12))
        
    # 3. Data Quality & Coverage Diagnostics
    story.append(Paragraph("2. Data Quality & Census Coverage Diagnostics", section_heading))
    q_rows = [
        [
            Paragraph("<b>Diagnostic Test</b>", ParagraphStyle("QHdr", parent=body_style, textColor=CLR_WHITE, fontName="Helvetica-Bold")),
            Paragraph("<b>Score / Index</b>", ParagraphStyle("QHdr", parent=body_style, textColor=CLR_WHITE, fontName="Helvetica-Bold")),
            Paragraph("<b>Status</b>", ParagraphStyle("QHdr", parent=body_style, textColor=CLR_WHITE, fontName="Helvetica-Bold")),
            Paragraph("<b>Demographic Interpretation & Recommendations</b>", ParagraphStyle("QHdr", parent=body_style, textColor=CLR_WHITE, fontName="Helvetica-Bold")),
        ]
    ]
    for q_code, q in result.quality_checks.items():
        score_str = f"{q.score:.2f}" if q.score is not None else "N/A"
        q_rows.append([
            Paragraph(f"<b>{_esc(q.name)}</b>", body_style),
            Paragraph(score_str, body_style),
            Paragraph(f"<b>{_esc(q.status)}</b>", body_style),
            Paragraph(f"{_esc(q.interpretation)}<br/><font color='#7C807A'><i>{_esc(q.recommendation)}</i></font>", muted_style),
        ])
        
    t_qual = Table(q_rows, colWidths=[2.2 * inch, 0.9 * inch, 1.0 * inch, 3.4 * inch])
    t_qual.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), CLR_TERRACOTTA),
        ("GRID", (0, 0), (-1, -1), 0.5, CLR_BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [CLR_WHITE, colors.HexColor("#F8F4EE")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_qual)
    story.append(Spacer(1, 14))
    
    # 4. Demographic Measures by Section (Blocks A to D + Nuptiality + Migration)
    story.append(Paragraph("3. Core Demographic Measures Battery & Interpretations", section_heading))
    
    sections = [
        ("Block A: Sex Composition", ["MP", "SR", "SRB", "EXCESS_M"]),
        ("Block B: Age Structure & Dependency", ["ACR", "TDR", "CDR_CHILD", "OADR", "AI", "PSR", "MEDIAN_AGE", "CWR", "DENSITY", "GROWTH_RATE", "PCT_0_14", "PCT_15_64", "PCT_65P"]),
        ("Block C: Fertility & Reproduction", ["CBR", "MBR", "GFR", "ASFR", "TFR", "GRR", "NRR", "MAC", "PROP_FEMALE_BIRTHS", "GRR_SHORT"]),
        ("Block D: Mortality & Standardization", ["CDR", "CORRECTED_CDR", "NMR", "ENMR", "PNMR", "IMR", "CMR", "U5MR", "MMR", "ASDR", "DSDR", "SMR", "ISDR"]),
        ("Block E: Life Tables", ["E0", "E65", "45Q15"]),
        ("Block F: Nuptiality & Marital Dynamics", ["SMAM_FEMALE", "SMAM_MALE", "SPOUSAL_GAP", "CELIBACY", "CMRG", "CDVR", "GDVR", "GMR", "MEDIAN_AGE_MARRIAGE"]),
        ("Block G: Migration & Redistribution", ["NMRG", "MER", "IMRG", "OMRG", "GROSS_MIG", "NET_MIG", "MER_SIGNED"]),
        ("Block H: Stable & Stationary Population", ["LOTKA_R", "INTRINSIC_B", "INTRINSIC_D", "GEN_LEN", "R1", "R2", "MU", "ALPHA", "BETA", "R_QUAD", "T_QUAD"]),
    ]
    
    for section_title, codes in sections:
        sec_measures = [result.measures[c] for c in codes if c in result.measures]
        if not sec_measures:
            continue
            
        story.append(Paragraph(f"<b>{_esc(section_title)}</b>", sub_heading))
        
        # Table of measures
        m_rows = [
            [
                Paragraph("<b>Code</b>", ParagraphStyle("MHdr", parent=body_style, textColor=CLR_WHITE, fontName="Helvetica-Bold")),
                Paragraph("<b>Measure Name (Shortform)</b>", ParagraphStyle("MHdr", parent=body_style, textColor=CLR_WHITE, fontName="Helvetica-Bold")),
                Paragraph("<b>Computed Value</b>", ParagraphStyle("MHdr", parent=body_style, textColor=CLR_WHITE, fontName="Helvetica-Bold")),
                Paragraph("<b>Benchmark Status</b>", ParagraphStyle("MHdr", parent=body_style, textColor=CLR_WHITE, fontName="Helvetica-Bold")),
            ]
        ]
        for m in sec_measures:
            interp = m.interpretation or {}
            m_rows.append([
                Paragraph(f"<b>{_esc(m.code)}</b>", body_style),
                Paragraph(f"<b>{_esc(m.name)}</b>", body_style),
                Paragraph(f"<b>{_esc(m.formatted_value)}</b>", body_style),
                Paragraph(f"{_esc(interp.get('status', 'MODERATE'))}: {_esc(interp.get('label', 'Standard'))}", muted_style),
            ])
            
        t_m = Table(m_rows, colWidths=[1.0 * inch, 3.2 * inch, 1.8 * inch, 1.5 * inch])
        t_m.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), CLR_TEXT),
            ("GRID", (0, 0), (-1, -1), 0.5, CLR_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [CLR_WHITE, colors.HexColor("#F8F4EE")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_m)
        story.append(Spacer(1, 4))
        
        # Plain Demographic Interpretation Box at the end of each section!
        story.append(Paragraph("<b>Demographic Interpretations of Measures in this Section:</b>", ParagraphStyle("SubInterp", parent=body_style, textColor=CLR_TERRACOTTA, fontName="Helvetica-Bold")))
        for m in sec_measures:
            head, _, body = (m.interpretation_line or f"{m.shortform} = {m.value_text}").partition(" : ")
            story.append(Paragraph(f"• <b>{_esc(head)}</b> : {_esc(body)}", interp_style))
        story.append(Spacer(1, 10))
        
    doc.build(story)
    return buffer.getvalue()


def generate_summary_pdf_brief(
    result: DemographicPipelineResult,
    output_path: Optional[str] = None,
) -> bytes:
    """One- to two-page brief: headline summary, the top concerns, data-quality status and key strengths."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer if output_path is None else output_path, pagesize=letter,
                            leftMargin=44, rightMargin=44, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("BTitle", parent=styles["Normal"], fontName="Helvetica", fontSize=20, leading=25, textColor=CLR_TEXT)
    sub = ParagraphStyle("BSub", parent=styles["Normal"], fontName="Helvetica", fontSize=10, leading=14, textColor=CLR_TERRACOTTA, spaceAfter=10)
    h = ParagraphStyle("BH", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=12, leading=16, textColor=CLR_TEXT, spaceBefore=12, spaceAfter=6)
    body = ParagraphStyle("BBody", parent=styles["Normal"], fontName="Helvetica", fontSize=9.5, leading=14, textColor=CLR_TEXT)
    muted = ParagraphStyle("BMuted", parent=body, fontSize=8.5, leading=12, textColor=CLR_TEXT_MUTED)
    story = [Paragraph("Executive Brief", title),
             Paragraph(f"{_esc(result.dataset_name)}" + (f" | {_esc(result.year)}" if result.year else "")
                       + f" | {result.computable_count} of {result.total_measures_target} measures computed", sub),
             HRFlowable(width="100%", thickness=1, color=CLR_TERRACOTTA, spaceAfter=6),
             Paragraph("Summary", h), Paragraph(_esc(result.executive_summary.replace("**", "")), body)]
    story.append(Paragraph("Top concerns", h))
    if result.top_concerns:
        for c in result.top_concerns[:4]:
            story.append(Paragraph(f"<b>{_esc(c.get('title', ''))}</b> ({_esc(str(c.get('severity', '')).title())})", body))
            story.append(Paragraph(_esc(f"{c.get('description', '')} {c.get('recommendation', '')}"), muted))
            story.append(Spacer(1, 5))
    else:
        story.append(Paragraph("No measure or quality check was flagged as concerning.", body))
    story.append(Paragraph("Data quality", h))
    for q in result.quality_checks.values():
        if q.score is not None:
            story.append(Paragraph(f"<b>{_esc(q.name)}</b>: {q.score:.2f} ({_esc(str(q.status).title())}). {_esc(q.interpretation)}", muted))
            story.append(Spacer(1, 3))
    if result.key_strengths:
        story.append(Paragraph("Key strengths", h))
        for st_ in result.key_strengths[:4]:
            story.append(Paragraph(f"{_esc(st_.get('title', ''))}", muted))
    doc.build(story)
    return buffer.getvalue()


def generate_section_pdf_report(
    section_name: str,
    measures: List[Any],
    dataset_name: str,
    year: Optional[int] = None,
    output_path: Optional[str] = None,
) -> bytes:
    """Generates a focused 1-page PDF report for a single syllabus section (R7)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer if output_path is None else output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("SecTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=CLR_TEXT, alignment=TA_LEFT)
    meta_style = ParagraphStyle("SecMeta", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10, textColor=CLR_TERRACOTTA)
    body_style = ParagraphStyle("SecBody", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=12, textColor=CLR_TEXT)
    
    story = [
        Paragraph(f"{_esc(section_name)} Statistical Report", title_style),
        Spacer(1, 4),
        Paragraph(f"Dataset: {_esc(dataset_name)} {f'({year})' if year else ''} &bull; Vital Statistics Suite", meta_style),
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=1, color=CLR_TERRACOTTA, spaceAfter=12),
    ]
    
    m_rows = [[
        Paragraph("<b>Code</b>", body_style),
        Paragraph("<b>Measure Name (Shortform)</b>", body_style),
        Paragraph("<b>Value</b>", body_style),
    ]]
    for m in measures:
        m_rows.append([
            Paragraph(f"<b>{_esc(m.code)}</b>", body_style),
            Paragraph(_esc(m.name), body_style),
            Paragraph(f"<b>{_esc(m.formatted_value)}</b>", body_style),
        ])
    t_m = Table(m_rows, colWidths=[1.2 * inch, 4.2 * inch, 2.1 * inch])
    t_m.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFE9DF")),
        ("GRID", (0, 0), (-1, -1), 0.5, CLR_BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [CLR_WHITE, colors.HexColor("#F8F4EE")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_m)
    story.append(Spacer(1, 14))
    
    story.append(Paragraph("<b>Demographic Interpretations:</b>", ParagraphStyle("SubInterp", parent=body_style, fontName="Helvetica-Bold", textColor=CLR_TERRACOTTA, fontSize=11)))
    story.append(Spacer(1, 4))
    for m in measures:
        head, _, body = (getattr(m, "interpretation_line", "") or f"{m.shortform} = {m.formatted_value}").partition(" : ")
        story.append(Paragraph(f"• <b>{_esc(head)}</b> : {_esc(body)}", body_style))
        story.append(Spacer(1, 4))
        
    doc.build(story)
    return buffer.getvalue()

