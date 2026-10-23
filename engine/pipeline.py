"""
Master Demographic Pipeline Orchestrator & Comparison Engine
Orchestrates:
1. Ingestion and quality audits (Whipple, Myers, UN Joint Score, PEC)
2. Calculation of all demographic measures across syllabus sections
3. Application of the Interpretation Layer (UN/WHO benchmarks + plain interpretations)
4. Executive synthesis: Top demographic concerns, key findings, and policy flags
5. Two-dataset comparative analysis and divergence audit
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

from engine.base import (
    DemographicMeasureResult,
    QualityCheckResult,
    DemographicDataset,
)
from engine.registry import MEASURES_CATALOGUE
from engine.sex_composition import compute_block_a
from engine.age_dependency import compute_block_b
from engine.fertility import compute_block_c
from engine.mortality import compute_block_d
from engine.nuptiality import compute_nuptiality_section
from engine.migration import compute_migration_section
from engine.stable import compute_stable_population_measures
from engine.quality import run_all_quality_checks
from engine.interpretation import interpret_measure, generate_section_interpretations


@dataclass
class DemographicPipelineResult:
    """Full execution output container for the Vital Stats Suite."""
    dataset_name: str
    year: Optional[int]
    region: Optional[str]
    quality_checks: Dict[str, QualityCheckResult]
    measures: Dict[str, DemographicMeasureResult]
    top_concerns: List[Dict[str, Any]]
    key_strengths: List[Dict[str, Any]]
    executive_summary: str
    computable_count: int
    total_measures_target: int = 0
    section_interpretations: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    def get_measure(self, code: str) -> Optional[DemographicMeasureResult]:
        return self.measures.get(code)

    def to_summary_dict(self) -> Dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "year": self.year,
            "region": self.region,
            "computable_count": self.computable_count,
            "total_measures_target": self.total_measures_target,
            "measures": {k: v.to_dict() for k, v in self.measures.items()},
            "quality_checks": {k: v.to_dict() for k, v in self.quality_checks.items()},
            "top_concerns": self.top_concerns,
            "key_strengths": self.key_strengths,
            "executive_summary": self.executive_summary,
            "section_interpretations": self.section_interpretations,
        }


@dataclass
class ComparisonResult:
    """Container for two-dataset comparative evaluation."""
    dataset_a_name: str
    dataset_b_name: str
    result_a: DemographicPipelineResult
    result_b: DemographicPipelineResult
    comparison_table: pd.DataFrame
    narrative_summary: str
    key_divergences: List[Dict[str, Any]]


def generate_executive_summary(
    measures: Dict[str, DemographicMeasureResult],
    quality_checks: Dict[str, QualityCheckResult],
    dataset_name: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """Generates the top demographic concerns, strengths, and editorial summary."""
    concerns: List[Dict[str, Any]] = []
    strengths: List[Dict[str, Any]] = []
    
    # 1. Quality checks alerts
    whipple = quality_checks.get("WHIPPLE")
    if whipple and whipple.status in ("WARNING", "SEVERE"):
        concerns.append({
            "title": f"Data Quality Alert: Age Heaping (Whipple's Index {whipple.score:.1f})",
            "measure": "WHIPPLE",
            "severity": whipple.status,
            "description": whipple.interpretation,
            "recommendation": whipple.recommendation,
        })
        
    un_score = quality_checks.get("UN_JOINT_SCORE")
    if un_score and un_score.status in ("WARNING", "SEVERE"):
        concerns.append({
            "title": f"Age-Sex Reporting Accuracy Alert (UN Joint Index {un_score.score:.1f})",
            "measure": "UN_JOINT_SCORE",
            "severity": un_score.status,
            "description": un_score.interpretation,
            "recommendation": un_score.recommendation,
        })
        
    pec = quality_checks.get("PEC")
    if pec and pec.status in ("WARNING", "SEVERE"):
        concerns.append({
            "title": f"Census Coverage Undercount ({pec.score:.1f}% Omission)",
            "measure": "PEC",
            "severity": pec.status,
            "description": pec.interpretation,
            "recommendation": pec.recommendation,
        })
        
    # 2. Demographic measure alerts
    for code, res in measures.items():
        interp = res.interpretation or {}
        st = interp.get("status", "")
        if st in ("CRITICAL", "CONCERNING"):
            concerns.append({
                "title": f"{res.name}: {res.formatted_value}",
                "measure": code,
                "severity": st,
                "description": interp.get("label", ""),
                "recommendation": res.plain_interpretation,
            })
        elif st in ("EXCELLENT", "GOOD"):
            strengths.append({
                "title": f"{res.name}: {res.formatted_value}",
                "measure": code,
                "severity": st,
                "description": interp.get("label", ""),
            })
            
    severity_order = {"CRITICAL": 0, "SEVERE": 1, "CONCERNING": 2, "WARNING": 3, "MODERATE": 4, "GOOD": 5, "EXCELLENT": 6}
    concerns.sort(key=lambda x: severity_order.get(x["severity"], 10))
    top_concerns = concerns[:4]
    
    # Narrative synthesis
    tfr = measures.get("TFR")
    imr = measures.get("IMR")
    tdr = measures.get("TDR")
    oadr = measures.get("OADR")
    sr = measures.get("SR")
    
    parts = [f"Comprehensive evaluation of **{dataset_name}** covers {len(measures)} computable demographic indicators."]
    if tfr:
        if tfr.raw_value < 1.5:
            parts.append(f"Fertility is at lowest-low sub-replacement levels (TFR {tfr.raw_value:.2f}), accelerating demographic aging.")
        elif tfr.raw_value < 2.1:
            parts.append(f"Fertility is below replacement level (TFR {tfr.raw_value:.2f}), signaling a transitioning population trajectory.")
        elif tfr.raw_value <= 2.5:
            parts.append(f"Fertility is near ideal demographic replacement (TFR {tfr.raw_value:.2f}).")
        else:
            parts.append(f"Fertility remains high (TFR {tfr.raw_value:.2f}), maintaining youthful population momentum.")
            
    if imr:
        if imr.raw_value <= 12.0:
            parts.append(f"Infant survival is strong (IMR {imr.raw_value:.1f} per 1,000 live births), meeting SDG Target 3.2.")
        else:
            parts.append(f"Infant mortality stands at {imr.raw_value:.1f} per 1,000 live births, indicating scope for improved neonatal health services.")
            
    if tdr and oadr:
        parts.append(f"The dependency load is {tdr.raw_value:.1f} per 100 workers, with elderly dependency at {oadr.raw_value:.1f}.")
        
    if sr and abs(sr.raw_value - 100.0) > 6.0:
        parts.append(f"The sex ratio shows noticeable skew ({sr.raw_value:.1f} males per 100 females).")
        
    summary_text = " ".join(parts)
    return top_concerns, strengths, summary_text


def run_demographic_pipeline(dataset: DemographicDataset) -> DemographicPipelineResult:
    """Executes the end-to-end demographic evaluation across all syllabus modules."""
    # 1. Run Data Quality Checks
    quality_checks = run_all_quality_checks(dataset)
    
    # 2. Compute Measures across all sections
    measures: Dict[str, DemographicMeasureResult] = {}
    
    block_a_res = compute_block_a(dataset)
    block_b_res = compute_block_b(dataset)
    block_c_res = compute_block_c(dataset)
    block_d_res = compute_block_d(dataset)
    nuptiality_res = compute_nuptiality_section(dataset)
    migration_res = compute_migration_section(dataset)
    
    measures.update(block_a_res)
    measures.update(block_b_res)
    measures.update(block_c_res)
    measures.update(block_d_res)
    measures.update(nuptiality_res)
    measures.update(migration_res)
    
    # Stable population if both fertility and mortality schedules exist
    if (dataset.fertility_schedule is not None and not dataset.fertility_schedule.empty and
        dataset.mortality_schedule is not None and not dataset.mortality_schedule.empty):
        try:
            stable_res = compute_stable_population_measures(dataset.fertility_schedule, dataset.mortality_schedule)
            measures.update(stable_res)
        except Exception:
            pass
            
    # 3. Apply Interpretation Layer
    for code, m in measures.items():
        interpret_measure(m)
        
    # 4. Generate Section-by-Section Plain Interpretations (for the end-of-section cards!)
    section_interps = {
        "A_COMPOSITION": generate_section_interpretations(list(block_a_res.values())),
        "B_AGE_STRUCTURE": generate_section_interpretations(list(block_b_res.values())),
        "C_FERTILITY": generate_section_interpretations(list(block_c_res.values())),
        "D_MORTALITY": generate_section_interpretations(list(block_d_res.values())),
        "F_NUPTIALITY": generate_section_interpretations(list(nuptiality_res.values())),
        "G_MIGRATION": generate_section_interpretations(list(migration_res.values())),
    }
    
    # 5. Synthesize Executive Synthesis
    concerns, strengths, summary = generate_executive_summary(measures, quality_checks, dataset.name)
    
    from engine.extra_measures import dataset_computable_count
    total_target = dataset_computable_count()
    
    return DemographicPipelineResult(
        dataset_name=dataset.name,
        year=dataset.year,
        region=dataset.region,
        quality_checks=quality_checks,
        measures=measures,
        top_concerns=concerns,
        key_strengths=strengths,
        executive_summary=summary,
        computable_count=len(measures),
        total_measures_target=total_target,
        section_interpretations=section_interps,
    )


def compare_two_datasets(
    dataset_a: DemographicDataset,
    dataset_b: DemographicDataset,
) -> ComparisonResult:
    """Executes pipeline on both datasets and computes side-by-side comparative diffs."""
    res_a = run_demographic_pipeline(dataset_a)
    res_b = run_demographic_pipeline(dataset_b)
    
    all_codes = sorted(list(set(res_a.measures.keys()) | set(res_b.measures.keys())))
    
    rows = []
    divergences = []
    
    for code in all_codes:
        m_a = res_a.measures.get(code)
        m_b = res_b.measures.get(code)
        name = m_a.name if m_a else (m_b.name if m_b else code)
        block = m_a.block if m_a else (m_b.block if m_b else "General")
        unit = m_a.unit if m_a else (m_b.unit if m_b else "")
        
        val_a = m_a.raw_value if m_a else None
        val_b = m_b.raw_value if m_b else None
        
        if val_a is not None and val_b is not None:
            delta = val_b - val_a
            pct_change = (delta / abs(val_a) * 100.0) if val_a != 0 else 0.0
            fmt_a = m_a.formatted_value
            fmt_b = m_b.formatted_value
            status_a = m_a.interpretation.get("status") if m_a.interpretation else "-"
            status_b = m_b.interpretation.get("status") if m_b.interpretation else "-"
            
            if abs(pct_change) >= 5.0 or (status_a != status_b):
                divergences.append({
                    "code": code,
                    "name": name,
                    "val_a": val_a,
                    "val_b": val_b,
                    "delta": delta,
                    "pct_change": pct_change,
                    "status_a": status_a,
                    "status_b": status_b,
                })
        else:
            delta = None
            pct_change = None
            fmt_a = m_a.formatted_value if m_a else "Not Computed"
            fmt_b = m_b.formatted_value if m_b else "Not Computed"
            status_a = m_a.interpretation.get("status", "-") if (m_a and m_a.interpretation) else "-"
            status_b = m_b.interpretation.get("status", "-") if (m_b and m_b.interpretation) else "-"
            
        rows.append({
            "Block": block,
            "Measure": name,
            "Code": code,
            f"{res_a.dataset_name} ({res_a.year or 'A'})": fmt_a,
            f"{res_b.dataset_name} ({res_b.year or 'B'})": fmt_b,
            "Delta": f"{delta:+.2f}" if delta is not None else "-",
            "Pct Change (%)": f"{pct_change:+.1f}%" if pct_change is not None else "-",
            "Status A": status_a,
            "Status B": status_b,
        })
        
    comp_df = pd.DataFrame(rows)
    
    narrative = (
        f"Comparative evaluation between **{res_a.dataset_name}** and **{res_b.dataset_name}** "
        f"identifies {len(divergences)} significant shifts (change of 5% or more, or a change in benchmark classification). "
    )
    
    return ComparisonResult(
        dataset_a_name=res_a.dataset_name,
        dataset_b_name=res_b.dataset_name,
        result_a=res_a,
        result_b=res_b,
        comparison_table=comp_df,
        narrative_summary=narrative,
        key_divergences=divergences,
    )
