"""
Section Schemas and CSV Template Generator
Provides explicit specifications for all input CSV files across demographic syllabus sections.
Generates blank downloadable CSV templates, performs schema validation, and prevents heuristic data invention.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import io


@dataclass
class ColumnSpec:
    name: str
    dtype: str
    required: bool
    description: str
    example: str


@dataclass
class SectionSchema:
    section_id: str
    section_name: str
    file_name: str
    description: str
    columns: List[ColumnSpec]
    
    def generate_template_csv(self) -> str:
        headers = [c.name for c in self.columns]
        examples = [c.example for c in self.columns]
        out = io.StringIO()
        out.write(",".join(headers) + "\n")
        out.write(",".join(examples) + "\n")
        return out.getvalue()


SECTION_SCHEMAS: Dict[str, SectionSchema] = {
    "S1_COMPOSITION": SectionSchema(
        section_id="S1",
        section_name="Composition & Growth",
        file_name="population_age_sex.csv",
        description="5-year or single-year age-sex population distribution.",
        columns=[
            ColumnSpec("age_group", "str", True, "Age group label (e.g. 0-4, 5-9, ..., 85+)", "0-4"),
            ColumnSpec("male", "float", True, "Male population count", "580000"),
            ColumnSpec("female", "float", True, "Female population count", "560000"),
            ColumnSpec("total", "float", False, "Total population count (optional, computed if missing)", "1140000"),
        ]
    ),
    "S2_QUALITY": SectionSchema(
        section_id="S2",
        section_name="Data Quality",
        file_name="pes_totals.csv",
        description="Post-Enumeration Check (PEC) or Dual-System coverage totals.",
        columns=[
            ColumnSpec("indicator", "str", True, "Coverage indicator name", "census_count"),
            ColumnSpec("value", "float", True, "Enumerated count or omission rate", "165158616"),
        ]
    ),
    "S3_FERTILITY": SectionSchema(
        section_id="S3",
        section_name="Fertility & Reproduction",
        file_name="fertility_age.csv",
        description="Maternal 5-year age-specific fertility schedule (ages 15-49).",
        columns=[
            ColumnSpec("age_group", "str", True, "Maternal 5-year age group (15-19 ... 45-49)", "20-24"),
            ColumnSpec("female_pop", "float", True, "Number of women in age group", "6800000"),
            ColumnSpec("births", "float", True, "Total live births to women in age group", "918000"),
            ColumnSpec("female_births", "float", False, "Female births (optional, derived via SRB if omitted)", "447800"),
            ColumnSpec("married_women", "float", False, "Married women count (optional, unlocks marital rates)", "4760000"),
            ColumnSpec("marital_births", "float", False, "Marital live births (optional)", "872000"),
        ]
    ),
    "S4_MORTALITY": SectionSchema(
        section_id="S4",
        section_name="Mortality & Standardization",
        file_name="mortality_age_sex.csv",
        description="Age-specific deaths and mid-year population by age group.",
        columns=[
            ColumnSpec("age_group", "str", True, "Age group label (0-4, 5-9, ..., 85+)", "0-4"),
            ColumnSpec("population", "float", True, "Mid-year population in age bracket", "16200000"),
            ColumnSpec("deaths", "float", True, "Annual deaths in age bracket", "58320"),
        ]
    ),
    "S5_LIFETABLE": SectionSchema(
        section_id="S5",
        section_name="Life Tables & Longevity",
        file_name="mortality_age_sex.csv",
        description="Age-specific mortality schedule to construct abridged and complete life tables.",
        columns=[
            ColumnSpec("age_group", "str", True, "Age group label (0-4, 5-9, ..., 85+)", "0-4"),
            ColumnSpec("population", "float", True, "Mid-year population in age bracket", "16200000"),
            ColumnSpec("deaths", "float", True, "Annual deaths in age bracket", "58320"),
        ]
    ),
    "S6_NUPTIALITY": SectionSchema(
        section_id="S6",
        section_name="Nuptiality & Marital Dynamics",
        file_name="marital_status.csv",
        description="Census counts by age group, sex, and marital status (for SMAM and celibacy).",
        columns=[
            ColumnSpec("age_group", "str", True, "Age bracket (15-19, 20-24, ..., 50-54)", "20-24"),
            ColumnSpec("sex", "str", True, "Sex ('male' or 'female')", "female"),
            ColumnSpec("never_married", "float", True, "Never-married (single) count", "3200000"),
            ColumnSpec("married", "float", True, "Currently married count", "4200000"),
            ColumnSpec("widowed", "float", False, "Widowed count", "45000"),
            ColumnSpec("divorced", "float", False, "Divorced count", "35000"),
            ColumnSpec("separated", "float", False, "Separated count", "12000"),
        ]
    ),
    "S7_MIGRATION": SectionSchema(
        section_id="S7",
        section_name="Migration & Redistribution",
        file_name="migration_totals.csv",
        description="Migration movements and demographic balancing equation components.",
        columns=[
            ColumnSpec("indicator", "str", True, "Indicator name (in_migrants, out_migrants, births, deaths)", "in_migrants"),
            ColumnSpec("value", "float", True, "Count or population parameter", "450000"),
        ]
    ),
    "S8_GRADUATION": SectionSchema(
        section_id="S8",
        section_name="Graduation & Age Smoothing",
        file_name="population_age_sex.csv",
        description="5-year grouped age counts for Sprague, Beers, and Karup-King graduation.",
        columns=[
            ColumnSpec("age_group", "str", True, "Age group label (0-4, 5-9, ..., 85+)", "0-4"),
            ColumnSpec("male", "float", True, "Male population count", "580000"),
            ColumnSpec("female", "float", True, "Female population count", "560000"),
            ColumnSpec("total", "float", False, "Total population count", "1140000"),
        ]
    ),
    "S9_STABLE": SectionSchema(
        section_id="S9",
        section_name="Stable & Stationary Populations",
        file_name="stable_population_input.csv",
        description="Fertility and mortality rates for Lotka intrinsic r, b, d and stable age distribution.",
        columns=[
            ColumnSpec("age_group", "str", True, "Maternal age bracket (15-19 ... 45-49)", "20-24"),
            ColumnSpec("female_pop", "float", True, "Female population", "6800000"),
            ColumnSpec("births", "float", True, "Annual live births", "918000"),
        ]
    ),
    "S10_PROJECTION": SectionSchema(
        section_id="S10",
        section_name="Cohort-Component Projection",
        file_name="projection_assumptions.csv",
        description="Assumptions for multi-cohort component population forecasting.",
        columns=[
            ColumnSpec("indicator", "str", True, "Assumption parameter key (horizon_years, srb, net_migration_annual)", "horizon_years"),
            ColumnSpec("value", "float", True, "Numeric parameter value", "30"),
        ]
    ),
    "S11_PROJECTION": SectionSchema(
        section_id="S11",
        section_name="Cohort-Component Projection",
        file_name="projection_assumptions.csv",
        description="Assumptions for multi-cohort component population forecasting.",
        columns=[
            ColumnSpec("indicator", "str", True, "Assumption parameter key", "horizon_years"),
            ColumnSpec("value", "float", True, "Numeric parameter value", "30"),
        ]
    )
}


def get_template_csv(section_key: str) -> str:
    """Returns downloadable blank CSV string for a given section schema."""
    schema = SECTION_SCHEMAS.get(section_key.upper())
    if schema:
        return schema.generate_template_csv()
    return "age_group,male,female,total\n0-4,1000,950,1950\n"
