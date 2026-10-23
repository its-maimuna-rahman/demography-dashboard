"""
Module 2: Inference & Policy Engine (Bridge to Cohort-Component Engine)
Maintains backward compatibility for tests and UI while delegating to engine.projection.
"""

from __future__ import annotations
import pandas as pd
from engine.projection import (
    PolicyFlag,
    CohortComponentProjectionResult,
    run_cohort_component_projection,
    simulate_demographic_trajectory,
)

# Export names
__all__ = [
    "PolicyFlag",
    "CohortComponentProjectionResult",
    "run_cohort_component_projection",
    "simulate_demographic_trajectory",
]
