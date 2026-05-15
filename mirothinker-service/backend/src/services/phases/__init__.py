"""MiroThinker - Three-Phase Research Loop

PLANNING → DEEP ANALYSIS → SYNTHESIS

Each phase is a separate module that can be independently tested and configured.
ResearchMemory is the single cross-phase information carrier.
"""

from src.services.phases.planning import PlanningPhase, ResearchPlan
from src.services.phases.deep_analysis import DeepAnalysisPhase
from src.services.phases.synthesis import SynthesisPhase

__all__ = [
    "PlanningPhase",
    "ResearchPlan",
    "DeepAnalysisPhase",
    "SynthesisPhase",
]
