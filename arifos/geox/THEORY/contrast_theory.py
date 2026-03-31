"""
GEOX Theory of Anomalous Contrast (ToAC) — Core Definitions
DITEMPA BUKAN DIBERI

Definition:
Anomalous Contrast is the systematic error that occurs when visual/display contrast
(how something looks) is conflated with physical contrast (what the signal actually is).
"""

from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class ContrastDomain(str, Enum):
    PHYSICAL = "physical"      # Earth TRUTH (Impedance, Discontinuity)
    DISPLAY = "display"        # Visualization (Colormap, Gain, Filter)
    PERCEPTUAL = "perceptual"  # Human/Agent recognition (Edges, Patterns)

class ContrastCanon(BaseModel):
    """The mandatory rules for governed interpretation."""
    rules: List[str] = [
        "C1: Never interpret single-view contrast.",
        "C2: Cross-validate multiple visual transforms.",
        "C3: Explicitly map visual proxies to physical axes.",
        "C4: Cap confidence if physical resolution < visual saliency."
    ]

class ToACCore:
    @staticmethod
    def identify_conflation_risk(physical_axes: List[str], display_transforms: List[str]) -> float:
        """Calculate Risk Level (0.0 - 1.0). High risk if complex transforms used."""
        return min(1.0, len(display_transforms) * 0.2 + 0.1)
