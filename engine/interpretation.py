"""
Demographic Interpretation Layer & Benchmark Standards
Maps all demographic measures to standard global benchmarks (UN DESA, WHO, PRB, CDC),
providing neutral qualitative classifications (e.g. Replacement Level, Sub-Replacement, High Fertility),
bell-curve gauge mapping parameters, and rigorous plain-language interpretation sentences for every measure.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, List
from engine.base import DemographicMeasureResult
from engine.registry import get_measure_meta, generate_measure_interpretation, format_measure_name


# Authoritative Benchmark Registry with Citations and Sourced Bands
# Adheres to B23: Neutral regime labels for demographic states; clinical labels for health outcomes
BENCHMARK_REGISTRY: Dict[str, Dict[str, Any]] = {
    "MP": {
        "name": "Masculinity Proportion (MP)",
        "unit": "%",
        "source": "UN DESA / Biological Baseline",
        "is_heuristic": False,
        "gauge_range": (45.0, 56.0),
        "bands": [
            {"max": 48.0, "status": "CONCERNING", "label": "Male Deficit (Heavy female surplus / out-migration)", "color": "#4A6B82"},
            {"min": 48.0, "max": 49.5, "status": "MODERATE", "label": "Slight Female Surplus (Normal in aging populations)", "color": "#7E9AA8"},
            {"min": 49.5, "max": 51.5, "status": "EXCELLENT", "label": "Balanced Sex Proportion (Biological baseline equilibrium)", "color": "#CC785C"},
            {"min": 51.5, "max": 53.0, "status": "MODERATE", "label": "Slight Male Surplus (Immigration / high SRB)", "color": "#DDA15E"},
            {"min": 53.0, "status": "CRITICAL", "label": "Severe Male Surplus (Son preference / selective migration)", "color": "#C05621"}
        ]
    },
    "SR": {
        "name": "Sex Ratio (SR)",
        "unit": "males per 100 females",
        "source": "UN Population Division Standards",
        "is_heuristic": False,
        "gauge_range": (85.0, 120.0),
        "bands": [
            {"max": 92.0, "status": "CONCERNING", "label": "Low Sex Ratio (Significant male deficit / war mortality / migration)", "color": "#4A6B82"},
            {"min": 92.0, "max": 97.0, "status": "MODERATE", "label": "Slight Female Excess (Typical in older demographics)", "color": "#7E9AA8"},
            {"min": 97.0, "max": 105.0, "status": "EXCELLENT", "label": "Balanced Sex Ratio (Optimal equilibrium)", "color": "#CC785C"},
            {"min": 105.0, "max": 110.0, "status": "MODERATE", "label": "Elevated Male Ratio", "color": "#DDA15E"},
            {"min": 110.0, "status": "CRITICAL", "label": "Skewed Male Surplus (Severe sex selection or labor migration)", "color": "#C05621"}
        ]
    },
    "SRB": {
        "name": "Sex Ratio at Birth (SRB)",
        "unit": "male births per 100 female births",
        "source": "UN DESA Biological Reference (Normal Band: 103-107)",
        "is_heuristic": False,
        "gauge_range": (98.0, 120.0),
        "bands": [
            {"max": 103.0, "status": "MODERATE", "label": "Low SRB (Below biological normal)", "color": "#7E9AA8"},
            {"min": 103.0, "max": 107.0, "status": "EXCELLENT", "label": "Normal Biological SRB (103-107)", "color": "#CC785C"},
            {"min": 107.0, "max": 112.0, "status": "CONCERNING", "label": "Elevated SRB (Potential sex selection)", "color": "#DDA15E"},
            {"min": 112.0, "status": "CRITICAL", "label": "Severely Skewed SRB (Active prenatal sex selection)", "color": "#C05621"}
        ]
    },
    "EXCESS_M": {
        "name": "Excess of Males (EXCESS_M)",
        "unit": "persons",
        "source": "Demographic Balance Standard",
        "is_heuristic": True,
        "gauge_range": (-5.0, 5.0),
        "bands": [
            {"max": -2.0, "status": "MODERATE", "label": "Female Majority", "color": "#7E9AA8"},
            {"min": -2.0, "max": 2.0, "status": "EXCELLENT", "label": "Balanced Sex Distribution", "color": "#CC785C"},
            {"min": 2.0, "status": "MODERATE", "label": "Male Majority", "color": "#DDA15E"}
        ]
    },
    "ACR": {
        "name": "Age Composition Ratio (ACR)",
        "unit": "% working age (15-64)",
        "source": "UN Demographic Dividend Framework",
        "is_heuristic": False,
        "gauge_range": (45.0, 75.0),
        "bands": [
            {"max": 55.0, "status": "CONCERNING", "label": "High Dependency Burden (Narrow working-age share)", "color": "#C05621"},
            {"min": 55.0, "max": 60.0, "status": "MODERATE", "label": "Moderate Productive Base", "color": "#DDA15E"},
            {"min": 60.0, "max": 68.0, "status": "EXCELLENT", "label": "Prime Demographic Dividend Window", "color": "#CC785C"},
            {"min": 68.0, "status": "GOOD", "label": "Peak Productive Ratio (Precedes aging transition)", "color": "#2A9D8F"}
        ]
    },
    "TDR": {
        "name": "Total Dependency Ratio (TDR)",
        "unit": "dependents per 100 workers",
        "source": "World Bank / UN Population Division",
        "is_heuristic": False,
        "gauge_range": (25.0, 100.0),
        "bands": [
            {"max": 45.0, "status": "EXCELLENT", "label": "Low Total Dependency (Optimal economic window)", "color": "#CC785C"},
            {"min": 45.0, "max": 55.0, "status": "GOOD", "label": "Moderate Dependency Load", "color": "#2A9D8F"},
            {"min": 55.0, "max": 70.0, "status": "MODERATE", "label": "Elevated Dependency Burden", "color": "#DDA15E"},
            {"min": 70.0, "status": "CRITICAL", "label": "Heavy Dependency Burden (High economic strain)", "color": "#C05621"}
        ]
    },
    "CDR_CHILD": {
        "name": "Child Dependency Ratio (CDR_CHILD)",
        "unit": "children per 100 workers",
        "source": "UN Population Division",
        "is_heuristic": False,
        "gauge_range": (15.0, 90.0),
        "bands": [
            {"max": 25.0, "status": "GOOD", "label": "Low Youth Dependency (Advanced transition)", "color": "#2A9D8F"},
            {"min": 25.0, "max": 45.0, "status": "EXCELLENT", "label": "Moderate Youth Dependency", "color": "#CC785C"},
            {"min": 45.0, "max": 65.0, "status": "MODERATE", "label": "High Youth Dependency (Educational investment needed)", "color": "#DDA15E"},
            {"min": 65.0, "status": "CRITICAL", "label": "Heavy Child Dependency Burden (Youth bulge)", "color": "#C05621"}
        ]
    },
    "OADR": {
        "name": "Old-Age Dependency Ratio (OADR)",
        "unit": "seniors per 100 workers",
        "source": "OECD / UN Aging Standards",
        "is_heuristic": False,
        "gauge_range": (5.0, 50.0),
        "bands": [
            {"max": 10.0, "status": "GOOD", "label": "Youthful Population (Minimal pension pressure)", "color": "#2A9D8F"},
            {"min": 10.0, "max": 20.0, "status": "EXCELLENT", "label": "Moderate Aging (Sustainable elder support)", "color": "#CC785C"},
            {"min": 20.0, "max": 35.0, "status": "MODERATE", "label": "Aging Society (Growing healthcare/pension liability)", "color": "#DDA15E"},
            {"min": 35.0, "status": "CRITICAL", "label": "Hyper-Aged Society (Severe pension/care workforce deficit)", "color": "#C05621"}
        ]
    },
    "AI": {
        "name": "Ageing Index (AI)",
        "unit": "elderly per 100 children",
        "source": "UN Population Division Aging Standard",
        "is_heuristic": False,
        "gauge_range": (10.0, 150.0),
        "bands": [
            {"max": 30.0, "status": "GOOD", "label": "Young Age Structure (AI < 30)", "color": "#2A9D8F"},
            {"min": 30.0, "max": 60.0, "status": "EXCELLENT", "label": "Transitional Age Structure (AI 30-60)", "color": "#CC785C"},
            {"min": 60.0, "max": 100.0, "status": "MODERATE", "label": "Aging Population (AI 60-100)", "color": "#DDA15E"},
            {"min": 100.0, "status": "CRITICAL", "label": "Elderly Outnumber Children (AI > 100)", "color": "#C05621"}
        ]
    },
    "CBR": {
        "name": "Crude Birth Rate (CBR)",
        "unit": "births per 1,000",
        "source": "UN Demographic Yearbook / World Bank",
        "is_heuristic": False,
        "gauge_range": (5.0, 45.0),
        "bands": [
            {"max": 10.0, "status": "CONCERNING", "label": "Very Low CBR (Population decline trajectory)", "color": "#C05621"},
            {"min": 10.0, "max": 16.0, "status": "GOOD", "label": "Low CBR (Modern demographic regime)", "color": "#2A9D8F"},
            {"min": 16.0, "max": 25.0, "status": "EXCELLENT", "label": "Moderate CBR (Sustainable replacement pace)", "color": "#CC785C"},
            {"min": 25.0, "max": 35.0, "status": "MODERATE", "label": "High CBR (Rapid population expansion)", "color": "#DDA15E"},
            {"min": 35.0, "status": "CONCERNING", "label": "Very High CBR (High maternal health burden)", "color": "#C05621"}
        ]
    },
    "MBR": {
        "name": "General Marital Fertility Rate (GMFR)",
        "unit": "births per 1,000 married women",
        "source": "Bhende & Kanitkar (2010)",
        "is_heuristic": True,
        "gauge_range": (40.0, 250.0),
        "bands": [
            {"max": 80.0, "status": "GOOD", "label": "Low Marital Fertility (Widespread family planning)", "color": "#2A9D8F"},
            {"min": 80.0, "max": 140.0, "status": "EXCELLENT", "label": "Moderate Marital Fertility", "color": "#CC785C"},
            {"min": 140.0, "max": 200.0, "status": "MODERATE", "label": "Elevated Marital Fertility", "color": "#DDA15E"},
            {"min": 200.0, "status": "CONCERNING", "label": "High Marital Fertility (Natural fertility regime)", "color": "#C05621"}
        ]
    },
    "GFR": {
        "name": "General Fertility Rate (GFR)",
        "unit": "births per 1,000 women (15-49)",
        "source": "CDC / National Vital Statistics System",
        "is_heuristic": False,
        "gauge_range": (30.0, 180.0),
        "bands": [
            {"max": 50.0, "status": "CONCERNING", "label": "Very Low GFR (Sub-replacement)", "color": "#C05621"},
            {"min": 50.0, "max": 75.0, "status": "GOOD", "label": "Low GFR", "color": "#2A9D8F"},
            {"min": 75.0, "max": 110.0, "status": "EXCELLENT", "label": "Near-Replacement GFR", "color": "#CC785C"},
            {"min": 110.0, "status": "MODERATE", "label": "High GFR", "color": "#DDA15E"}
        ]
    },
    "TFR": {
        "name": "Total Fertility Rate (TFR)",
        "unit": "children per woman",
        "source": "UN DESA Population Division (Replacement Level = 2.1)",
        "is_heuristic": False,
        "gauge_range": (0.8, 6.0),
        "bands": [
            {"max": 1.3, "status": "CRITICAL", "label": "Lowest-Low Fertility (TFR <= 1.3, severe contraction)", "color": "#C05621"},
            {"min": 1.3, "max": 1.8, "status": "CONCERNING", "label": "Sub-Replacement Fertility (1.3 < TFR < 1.8)", "color": "#DDA15E"},
            {"min": 1.8, "max": 2.2, "status": "EXCELLENT", "label": "Replacement Level (~2.1 children per woman)", "color": "#CC785C"},
            {"min": 2.2, "max": 3.5, "status": "GOOD", "label": "Moderate Growth Fertility (2.2 - 3.5)", "color": "#2A9D8F"},
            {"min": 3.5, "status": "CONCERNING", "label": "High Fertility (TFR > 3.5, rapid growth)", "color": "#C05621"}
        ]
    },
    "GRR": {
        "name": "Gross Reproduction Rate (GRR)",
        "unit": "daughters per woman",
        "source": "Preston et al. (2001), Ch. 5 (Replacement ~ 1.02)",
        "is_heuristic": False,
        "gauge_range": (0.4, 3.0),
        "bands": [
            {"max": 0.9, "status": "CONCERNING", "label": "Sub-Replacement Generation (< 0.9 daughters)", "color": "#C05621"},
            {"min": 0.9, "max": 1.1, "status": "EXCELLENT", "label": "Generational Replacement (~1.0 daughter per woman)", "color": "#CC785C"},
            {"min": 1.1, "status": "GOOD", "label": "Expanding Female Cohort (> 1.1 daughters)", "color": "#2A9D8F"}
        ]
    },
    "NRR": {
        "name": "Net Reproduction Rate (NRR)",
        "unit": "surviving daughters per woman",
        "source": "UN Population Division (Exact Replacement = 1.000)",
        "is_heuristic": False,
        "gauge_range": (0.4, 2.5),
        "bands": [
            {"max": 0.75, "status": "CRITICAL", "label": "Severe Sub-Replacement (NRR <= 0.75)", "color": "#C05621"},
            {"min": 0.75, "max": 0.95, "status": "CONCERNING", "label": "Below Replacement (0.75 < NRR < 0.95)", "color": "#DDA15E"},
            {"min": 0.95, "max": 1.05, "status": "EXCELLENT", "label": "Exact Generational Replacement (NRR ≈ 1.00)", "color": "#CC785C"},
            {"min": 1.05, "max": 1.50, "status": "GOOD", "label": "Moderate Generational Growth (1.05 - 1.50)", "color": "#2A9D8F"},
            {"min": 1.50, "status": "MODERATE", "label": "Rapid Generational Expansion (NRR > 1.50)", "color": "#DDA15E"}
        ]
    },
    "CDR": {
        "name": "Crude Death Rate (CDR)",
        "unit": "deaths per 1,000",
        "source": "WHO Global Health Observatory",
        "is_heuristic": False,
        "gauge_range": (3.0, 20.0),
        "bands": [
            {"max": 6.0, "status": "GOOD", "label": "Low CDR (Youthful population or strong health systems)", "color": "#2A9D8F"},
            {"min": 6.0, "max": 9.0, "status": "EXCELLENT", "label": "Moderate / Normal CDR", "color": "#CC785C"},
            {"min": 9.0, "max": 13.0, "status": "MODERATE", "label": "Elevated CDR (Often driven by older age structure)", "color": "#DDA15E"},
            {"min": 13.0, "status": "CRITICAL", "label": "High CDR (High epidemiological burden / elderly society)", "color": "#C05621"}
        ]
    },
    "CORRECTED_CDR": {
        "name": "Corrected Crude Death Rate (CCDR)",
        "unit": "adjusted deaths per 1,000",
        "source": "UN Principles and Recommendations for Vital Statistics",
        "is_heuristic": False,
        "gauge_range": (3.0, 25.0),
        "bands": [
            {"max": 7.0, "status": "GOOD", "label": "Low Adjusted Mortality", "color": "#2A9D8F"},
            {"min": 7.0, "max": 10.0, "status": "EXCELLENT", "label": "Normal Adjusted Mortality", "color": "#CC785C"},
            {"min": 10.0, "status": "MODERATE", "label": "Elevated Adjusted Mortality", "color": "#DDA15E"}
        ]
    },
    "NMR": {
        "name": "Neonatal Mortality Rate (NMR)",
        "unit": "deaths per 1,000 live births",
        "source": "WHO / UN SDG Target 3.2 (Goal: <= 12 per 1,000)",
        "is_heuristic": False,
        "gauge_range": (1.0, 45.0),
        "bands": [
            {"max": 5.0, "status": "EXCELLENT", "label": "Very Low (High-income clinical standard)", "color": "#CC785C"},
            {"min": 5.0, "max": 12.0, "status": "GOOD", "label": "SDG Target Achieved (<= 12.0 per 1,000)", "color": "#2A9D8F"},
            {"min": 12.0, "max": 25.0, "status": "CONCERNING", "label": "Elevated Neonatal Mortality (Above SDG Target)", "color": "#DDA15E"},
            {"min": 25.0, "status": "CRITICAL", "label": "Critical Neonatal Mortality (Urgent delivery/NICU interventions needed)", "color": "#C05621"}
        ]
    },
    "IMR": {
        "name": "Infant Mortality Rate (IMR)",
        "unit": "deaths per 1,000 live births",
        "source": "UNICEF / WHO Global Standards",
        "is_heuristic": False,
        "gauge_range": (1.5, 90.0),
        "bands": [
            {"max": 6.0, "status": "EXCELLENT", "label": "Exceptional Child Health (< 6 per 1,000)", "color": "#CC785C"},
            {"min": 6.0, "max": 15.0, "status": "GOOD", "label": "Low IMR (Good public health / immunization)", "color": "#2A9D8F"},
            {"min": 15.0, "max": 35.0, "status": "MODERATE", "label": "Moderate IMR", "color": "#DDA15E"},
            {"min": 35.0, "max": 60.0, "status": "CONCERNING", "label": "High IMR (Elevated preventable infant mortality)", "color": "#E76F51"},
            {"min": 60.0, "status": "CRITICAL", "label": "Critical IMR (Severe health/nutrition crisis)", "color": "#C05621"}
        ]
    },
    "CMR": {
        "name": "Child Death Rate (CDR 1-4)",
        "unit": "deaths per 1,000 children (1-4)",
        "source": "Preston et al. (2001); Shryock & Siegel (1976)",
        "is_heuristic": False,
        "gauge_range": (0.5, 20.0),
        "bands": [
            {"max": 1.5, "status": "EXCELLENT", "label": "Very Low Child Mortality", "color": "#CC785C"},
            {"min": 1.5, "max": 4.0, "status": "GOOD", "label": "Low Child Mortality", "color": "#2A9D8F"},
            {"min": 4.0, "max": 8.0, "status": "CONCERNING", "label": "Elevated Child Mortality", "color": "#DDA15E"},
            {"min": 8.0, "status": "CRITICAL", "label": "High Child Mortality", "color": "#C05621"}
        ]
    },
    "U5MR": {
        "name": "Under-5 Mortality Rate (U5MR)",
        "unit": "deaths per 1,000 live births",
        "source": "WHO / UN SDG Target 3.2.1 (Goal: <= 25 per 1,000)",
        "is_heuristic": False,
        "gauge_range": (2.0, 120.0),
        "bands": [
            {"max": 8.0, "status": "EXCELLENT", "label": "Very Low Under-5 Mortality (< 8 per 1,000)", "color": "#CC785C"},
            {"min": 8.0, "max": 25.0, "status": "GOOD", "label": "SDG Target Achieved (<= 25 per 1,000)", "color": "#2A9D8F"},
            {"min": 25.0, "max": 50.0, "status": "CONCERNING", "label": "Elevated Under-5 Mortality", "color": "#DDA15E"},
            {"min": 50.0, "status": "CRITICAL", "label": "High Under-5 Mortality", "color": "#C05621"}
        ]
    },
    "DSDR": {
        "name": "Direct Standardized Death Rate (DSDR)",
        "unit": "standardized deaths per 1,000",
        "source": "WHO Global Standardized Mortality Database",
        "is_heuristic": False,
        "gauge_range": (3.0, 20.0),
        "bands": [
            {"max": 5.5, "status": "EXCELLENT", "label": "Low Standardized Mortality", "color": "#CC785C"},
            {"min": 5.5, "max": 8.5, "status": "GOOD", "label": "Moderate Standardized Mortality", "color": "#2A9D8F"},
            {"min": 8.5, "max": 12.0, "status": "MODERATE", "label": "Elevated Standardized Mortality", "color": "#DDA15E"},
            {"min": 12.0, "status": "CRITICAL", "label": "High Standardized Mortality", "color": "#C05621"}
        ]
    },
    "SMR": {
        "name": "Standardized Mortality Ratio (SMR)",
        "unit": "ratio (Obs / Exp)",
        "source": "Epidemiologic Standard (Null = 1.00)",
        "is_heuristic": False,
        "gauge_range": (0.5, 2.0),
        "bands": [
            {"max": 0.85, "status": "EXCELLENT", "label": "Substantially Lower Mortality than Standard (SMR < 0.85)", "color": "#CC785C"},
            {"min": 0.85, "max": 1.15, "status": "GOOD", "label": "Comparable to Standard Mortality (0.85 - 1.15)", "color": "#2A9D8F"},
            {"min": 1.15, "max": 1.40, "status": "MODERATE", "label": "Elevated Relative Mortality (15-40% excess deaths)", "color": "#DDA15E"},
            {"min": 1.40, "status": "CRITICAL", "label": "Severe Excess Mortality (> 40% excess deaths)", "color": "#C05621"}
        ]
    },
    "ISDR": {
        "name": "Indirect Standardized Death Rate (ISDR)",
        "unit": "deaths per 1,000",
        "source": "Epidemiologic Standard",
        "is_heuristic": False,
        "gauge_range": (3.0, 20.0),
        "bands": [
            {"max": 6.0, "status": "EXCELLENT", "label": "Low Indirect Standardized Rate", "color": "#CC785C"},
            {"min": 6.0, "max": 9.0, "status": "GOOD", "label": "Moderate Indirect Rate", "color": "#2A9D8F"},
            {"min": 9.0, "status": "MODERATE", "label": "Elevated Indirect Rate", "color": "#DDA15E"}
        ]
    },
    "E0": {
        "name": "Life Expectancy at Birth (e0)",
        "unit": "years",
        "source": "UN DESA Population Division",
        "is_heuristic": False,
        "gauge_range": (50.0, 88.0),
        "bands": [
            {"max": 60.0, "status": "CRITICAL", "label": "Low Life Expectancy (< 60 years)", "color": "#C05621"},
            {"min": 60.0, "max": 70.0, "status": "MODERATE", "label": "Moderate Life Expectancy (60-70 years)", "color": "#DDA15E"},
            {"min": 70.0, "max": 78.0, "status": "GOOD", "label": "High Life Expectancy (70-78 years)", "color": "#2A9D8F"},
            {"min": 78.0, "status": "EXCELLENT", "label": "Very High Life Expectancy (> 78 years)", "color": "#CC785C"}
        ]
    },
    "SMAM_FEMALE": {
        "name": "Singulate Mean Age at Marriage — Female (SMAM-F)",
        "unit": "years",
        "source": "UN DESA Marriage Indicators; Hajnal (1953)",
        "is_heuristic": False,
        "gauge_range": (16.0, 32.0),
        "bands": [
            {"max": 19.0, "status": "CRITICAL", "label": "Prevalent Early / Child Marriage (< 19 years)", "color": "#C05621"},
            {"min": 19.0, "max": 22.0, "status": "CONCERNING", "label": "Young Age at Marriage (19-22 years)", "color": "#DDA15E"},
            {"min": 22.0, "max": 26.0, "status": "EXCELLENT", "label": "Moderate Age at Marriage (22-26 years)", "color": "#CC785C"},
            {"min": 26.0, "status": "GOOD", "label": "Delayed Marriage (> 26 years)", "color": "#2A9D8F"}
        ]
    },
    "SMAM_MALE": {
        "name": "Singulate Mean Age at Marriage — Male (SMAM-M)",
        "unit": "years",
        "source": "UN DESA Marriage Indicators",
        "is_heuristic": False,
        "gauge_range": (20.0, 36.0),
        "bands": [
            {"max": 23.0, "status": "MODERATE", "label": "Young Male Marriage (< 23 years)", "color": "#DDA15E"},
            {"min": 23.0, "max": 28.0, "status": "EXCELLENT", "label": "Normal Marriage Age (23-28 years)", "color": "#CC785C"},
            {"min": 28.0, "status": "GOOD", "label": "Delayed Male Marriage (> 28 years)", "color": "#2A9D8F"}
        ]
    },
}


def interpret_measure(result: DemographicMeasureResult) -> DemographicMeasureResult:
    """Attaches benchmark classification, status rating, gauge parameters, and narrative to result."""
    code = result.code
    val = result.raw_value
    
    # Ensure plain-language interpretation is generated if not yet set
    if not result.plain_interpretation:
        result.plain_interpretation = generate_measure_interpretation(code, val, result.inputs_used)
        
    spec = BENCHMARK_REGISTRY.get(code)
    if not spec:
        result.interpretation = {
            "status": "UNRATED",
            "label": "Custom Measure",
            "source": "Custom",
            "is_heuristic": True,
            "gauge_min": 0.0,
            "gauge_max": val * 1.5 if val > 0 else 100.0,
            "current_val": val,
            "plain_interpretation": result.plain_interpretation,
        }
        return result
        
    bands = spec["bands"]
    matched_band = None
    for b in bands:
        min_v = b.get("min", -float("inf"))
        max_v = b.get("max", float("inf"))
        if min_v <= val < max_v:
            matched_band = b
            break
            
    if matched_band is None and bands:
        matched_band = bands[-1] if val >= bands[-1].get("min", 0) else bands[0]
        
    g_min, g_max = spec["gauge_range"]
    
    result.interpretation = {
        "status": matched_band.get("status", "MODERATE"),
        "label": matched_band.get("label", "Standard"),
        "color": matched_band.get("color", "#CC785C"),
        "source": spec["source"],
        "is_heuristic": spec["is_heuristic"],
        "gauge_min": g_min,
        "gauge_max": g_max,
        "current_val": val,
        "unit": spec["unit"],
        "plain_interpretation": result.plain_interpretation,
    }
    return result


def generate_section_interpretations(measures: List[DemographicMeasureResult]) -> List[Dict[str, Any]]:
    """
    Produces the dedicated 'Interpretation of Measures' block for the end of a section.
    Returns structured list with code, display name (with shortform), formatted value, and plain demographic interpretation.
    """
    entries = []
    for m in measures:
        interp_text = m.plain_interpretation or generate_measure_interpretation(m.code, m.raw_value, m.inputs_used)
        entries.append({
            "line": m.interpretation_line,
            "code": m.code,
            "shortform": m.shortform or m.code,
            "name": m.name,  # contains Full Name (SHORTFORM)
            "value": m.raw_value,
            "formatted_value": m.formatted_value,
            "unit": m.unit,
            "interpretation": interp_text,
            "status": m.interpretation.get("status", "MODERATE") if m.interpretation else "COMPUTED",
        })
    return entries
