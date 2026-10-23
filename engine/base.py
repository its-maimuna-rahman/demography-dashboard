"""
Vital Stats Suite - Core Interfaces and Base Data Structures
Defines standardized data classes, result models, reference populations, and validation helpers.
Ensures every measure includes full name, shortform, formula, citation, and plain-language demographic interpretation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
import re
import numpy as np
import pandas as pd


# Standard World Population (WHO Standard 2000-2025 by 5-year age groups per 100,000)
WHO_STANDARD_POPULATION_5YR: Dict[str, float] = {
    "0-4": 8860,
    "5-9": 8690,
    "10-14": 8600,
    "15-19": 8470,
    "20-24": 8220,
    "25-29": 7930,
    "30-34": 7610,
    "35-39": 7150,
    "40-44": 6590,
    "45-49": 6040,
    "50-54": 5370,
    "55-59": 4550,
    "60-64": 3720,
    "65-69": 2960,
    "70-74": 2210,
    "75-79": 1520,
    "80-84": 910,
    "85+": 630,
}

# Standard World Population (Segi 1960 Standard Population per 100,000)
SEGI_STANDARD_POPULATION_5YR: Dict[str, float] = {
    "0-4": 12000,
    "5-9": 10000,
    "10-14": 9000,
    "15-19": 9000,
    "20-24": 8000,
    "25-29": 8000,
    "30-34": 6000,
    "35-39": 6000,
    "40-44": 6000,
    "45-49": 6000,
    "50-54": 5000,
    "55-59": 4000,
    "60-64": 4000,
    "65-69": 3000,
    "70-74": 2000,
    "75-79": 1000,
    "80-84": 500,
    "85+": 500,
}

# Reference WHO Standard ASDR schedule (deaths per 1,000 population)
WHO_STANDARD_ASDR_5YR: Dict[str, float] = {
    "0-4": 5.2,
    "5-9": 0.6,
    "10-14": 0.5,
    "15-19": 1.0,
    "20-24": 1.4,
    "25-29": 1.7,
    "30-34": 2.2,
    "35-39": 3.1,
    "40-44": 4.6,
    "45-49": 6.8,
    "50-54": 10.3,
    "55-59": 15.6,
    "60-64": 24.1,
    "65-69": 37.0,
    "70-74": 57.5,
    "75-79": 88.0,
    "80-84": 135.0,
    "85+": 215.0,
}


@dataclass
class DemographicMeasureResult:
    """
    Standard container for the result of any demographic calculation.
    Always includes shortform alongside full form (e.g. 'Gross Reproduction Rate (GRR)')
    and an explicit plain-language demographic interpretation.
    """
    code: str
    name: str  # Full name formatted with shortform: e.g. "Gross Reproduction Rate (GRR)"
    block: str
    raw_value: float
    formatted_value: str
    unit: str
    formula: str
    citation: str = ""
    shortform: str = ""
    full_name: str = ""
    plain_interpretation: str = ""
    status: str = "computed"  # 'computed', 'approximate', 'unavailable'
    interpretation: Optional[Dict[str, Any]] = None
    inputs_used: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[str] = None
    method: Optional[str] = None
    assumptions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    formula_latex: str = ""

    def __post_init__(self):
        if not self.formula_latex:
            from engine.formulas import latex_for
            self.formula_latex = latex_for(self.code)
        # Guarantee shortform and full_name are populated
        if not self.shortform:
            self.shortform = self.code
        if not self.full_name:
            if "(" in self.name and self.name.endswith(")"):
                self.full_name = self.name.split("(")[0].strip()
            else:
                self.full_name = self.name
        # Guarantee display name includes shortform: Full Name (SHORTFORM)
        if self.shortform and f"({self.shortform})" not in self.name:
            self.name = f"{self.full_name} ({self.shortform})"

    @property
    def value_text(self) -> str:
        """The bare number for headlines, e.g. '49.58' (no % sign or unit)."""
        m = re.match(r"^\s*([+\-]?[\d,]*\.?\d+)", str(self.formatted_value))
        if m:
            return m.group(1)
        try:
            return f"{float(self.raw_value):,.2f}"
        except (TypeError, ValueError):
            return str(self.formatted_value)

    @property
    def interpretation_line(self) -> str:
        """One-line reading in the form 'MP = 49.58 : Roughly 49.58% of the population is male.'"""
        body = self.plain_interpretation or ""
        return f"{self.shortform} = {self.value_text} : {body}".rstrip(" :")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "formula_latex": self.formula_latex,
            "interpretation_line": self.interpretation_line,
            "code": self.code,
            "shortform": self.shortform,
            "full_name": self.full_name,
            "name": self.name,
            "block": self.block,
            "raw_value": self.raw_value,
            "formatted_value": self.formatted_value,
            "unit": self.unit,
            "formula": self.formula,
            "citation": self.citation,
            "plain_interpretation": self.plain_interpretation,
            "status": self.status,
            "interpretation": self.interpretation,
            "inputs_used": self.inputs_used,
            "notes": self.notes,
            "method": self.method,
            "assumptions": self.assumptions,
            "warnings": self.warnings,
        }


@dataclass
class QualityCheckResult:
    """Standard container for demographic data quality evaluation."""
    check_code: str
    name: str
    score: Optional[float]
    status: str  # 'EXCELLENT', 'ACCEPTABLE', 'WARNING', 'SEVERE', 'MISSING_DATA'
    summary: str
    interpretation: str
    recommendation: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_code": self.check_code,
            "name": self.name,
            "score": self.score,
            "status": self.status,
            "summary": self.summary,
            "interpretation": self.interpretation,
            "recommendation": self.recommendation,
            "details": self.details,
        }


@dataclass
class DemographicDataset:
    """
    Standard tabular container for census, survey, or vital registration data.
    Supports age distributions, sex splits, fertility schedules, and mortality schedules.
    """
    name: str = "Demographic Dataset"
    year: Optional[int] = None
    region: Optional[str] = None
    area_km2: Optional[float] = None
    urban_population: Optional[float] = None
    
    # Population totals
    total_population: Optional[float] = None
    male_population: Optional[float] = None
    female_population: Optional[float] = None
    
    # Age group totals (Broad age groups)
    pop_0_14: Optional[float] = None
    pop_15_64: Optional[float] = None
    pop_65_plus: Optional[float] = None
    
    # Detailed tables
    single_year_ages: Optional[pd.DataFrame] = None
    age_group_5yr: Optional[pd.DataFrame] = None
    
    # Vital events totals
    total_live_births: Optional[float] = None
    male_births: Optional[float] = None
    female_births: Optional[float] = None
    marital_births: Optional[float] = None
    married_women_15_49: Optional[float] = None
    total_women_15_49: Optional[float] = None
    
    # Fertility schedule: columns ['age_group', 'female_pop', 'births', 'female_births' (opt)]
    fertility_schedule: Optional[pd.DataFrame] = None
    
    # Mortality counts
    total_deaths: Optional[float] = None
    male_deaths: Optional[float] = None
    female_deaths: Optional[float] = None
    neonatal_deaths: Optional[float] = None   # < 28 days
    early_neonatal_deaths: Optional[float] = None # < 7 days
    post_neonatal_deaths: Optional[float] = None  # 28 days - 1 year
    infant_deaths: Optional[float] = None     # < 1 year
    child_deaths_1_4: Optional[float] = None  # age 1-4
    pop_1_4: Optional[float] = None
    maternal_deaths: Optional[float] = None
    stillbirths: Optional[float] = None
    
    # Mortality schedule by age group: columns ['age_group', 'population', 'deaths']
    mortality_schedule: Optional[pd.DataFrame] = None
    
    # Life table fragment if provided: columns ['age_group', 'nLx', 'lx', 'p_survival']
    life_table_female: Optional[pd.DataFrame] = None
    
    # Standard population for age standardization
    standard_population: Optional[pd.DataFrame] = None
    standard_rates: Optional[pd.DataFrame] = None
    
    # Coverage and completeness factors (separate census vs death registration, B2)
    census_coverage_rate: Optional[float] = None       # e.g., 0.968 for 96.8% coverage
    pec_omission_rate: Optional[float] = None          # e.g., 0.032 for 3.2% undercount
    pec_completeness_rate: Optional[float] = None      # legacy alias for census_coverage_rate
    death_registration_completeness: Optional[float] = None  # e.g. 0.85 for 85% death completeness
    birth_registration_completeness: Optional[float] = None  # e.g. 0.90 for 90% birth completeness
    
    # Nuptiality & Marital Status counts
    marital_status_df: Optional[pd.DataFrame] = None
    marriages_total: Optional[float] = None
    first_marriages: Optional[float] = None
    divorces_total: Optional[float] = None
    marriages_df: Optional[pd.DataFrame] = None
    divorces_df: Optional[pd.DataFrame] = None
    
    # Migration counts
    in_migrants: Optional[float] = None
    out_migrants: Optional[float] = None
    net_migrants: Optional[float] = None
    migration_matrix_df: Optional[pd.DataFrame] = None
    migration_age_df: Optional[pd.DataFrame] = None
    
    # Historical / Multi-Census Series
    previous_census_pop: Optional[float] = None
    previous_census_year: Optional[int] = None
    
    # Metadata & Raw data dictionary
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_df: Optional[pd.DataFrame] = None

    def __post_init__(self):
        if self.pec_completeness_rate is not None and self.census_coverage_rate is None:
            self.census_coverage_rate = self.pec_completeness_rate
        elif self.census_coverage_rate is not None and self.pec_completeness_rate is None:
            self.pec_completeness_rate = self.census_coverage_rate
        if self.pec_omission_rate is not None and self.census_coverage_rate is None:
            self.census_coverage_rate = 1.0 - self.pec_omission_rate
