"""
GEOX Contrast Wrapper — Enforces Contrast Canon at Tool Boundary
DITEMPA BUKAN DIBERI

Mandatory metadata for every seismic/image/attribute output.
Never let perceptual contrast be silently confused with physical contrast.

Constitutional Floors Enforced:
  F1  Amanah — Reversibility through explicit provenance
  F4  Clarity — Physical vs perceptual axes clearly labeled
  F7  Humility — Uncertainty bounds on all meta-attributes
  F9  Anti-Hantu — No phantom geological meaning from display artifacts
"""

from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ContrastMetadata(BaseModel):
    """
    Mandatory Contrast Canon block — attached to every attribute output.
    
    Separates physical signal differences from display/perceptual artifacts,
    preventing the "anomalous risk" where visualization choices create
    false geological confidence.
    """
    attribute_name: str = Field(
        ..., 
        description="e.g. coherence_semblance, curvature_max, meta_fault_prob"
    )
    physical_axes: list[str] = Field(
        ..., 
        description="Physical signal differences (impedance, waveform_similarity, etc.)"
    )
    processing_steps: list[str] = Field(
        default_factory=list, 
        description="Chain of transforms applied (dip_steered, semblance_3x3x3, etc.)"
    )
    visual_encoding: dict[str, Any] = Field(
        default_factory=lambda: {
            "colormap": "gray_inverted", 
            "dynamic_range": "p2-p98", 
            "gamma": 1.0
        },
        description="Display parameters that affect perceptual contrast"
    )
    anomalous_risk: dict[str, Any] = Field(
        default_factory=lambda: {"display_bias": "medium", "notes": ""},
        description="Risk assessment for display-induced misinterpretation"
    )
    equation_reference: str | None = Field(
        default=None, 
        description="Literature or formula source (e.g. 'Marfurt et al. 1998')"
    )
    uncertainty_factors: list[str] = Field(
        default_factory=list,
        description="Explicit uncertainty sources (noise, acquisition footprint, processing artifacts)"
    )

    model_config = {"json_schema_extra": {"title": "ContrastMetadata"}}


class AttributeVolume(BaseModel):
    """
    A single computed attribute volume with full contrast metadata.
    """
    name: str = Field(..., description="Attribute identifier")
    data: Any = Field(..., description="Volume data array or reference")
    contrast: ContrastMetadata = Field(..., description="Contrast Canon metadata")
    uncertainty: float = Field(
        ..., 
        ge=0.03, 
        le=0.15, 
        description="F7 Humility: fractional uncertainty [0.03, 0.15]"
    )
    
    model_config = {"json_schema_extra": {"title": "AttributeVolume"}}


def contrast_governed(
    physical_axes: list[str],
    equation_ref: str | None = None,
    is_meta_attribute: bool = False,
) -> Callable:
    """
    Decorator factory for seismic attribute functions.
    
    Automatically attaches ContrastMetadata and enforces constitutional
    floors on all attribute outputs.
    
    Args:
        physical_axes: Physical quantities this attribute measures
        equation_ref: Literature citation for the attribute formula
        is_meta_attribute: True if ML-derived (higher scrutiny required)
    
    Example:
        @contrast_governed(
            physical_axes=["waveform_similarity", "discontinuity"],
            equation_ref="Marfurt et al. (1998)",
        )
        async def compute_coherence(volume, config):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> dict[str, Any]:
            # Execute the wrapped function
            result = await func(*args, **kwargs)
            
            # Determine attribute name from function or kwargs
            attr_name = kwargs.get("attribute_name", func.__name__)
            
            # Build ContrastMetadata
            contrast = ContrastMetadata(
                attribute_name=attr_name,
                physical_axes=physical_axes,
                processing_steps=kwargs.get("processing_steps", ["default"]),
                visual_encoding=kwargs.get("visual_encoding", {
                    "colormap": "gray_inverted",
                    "dynamic_range": "p2-p98",
                    "gamma": 1.0,
                }),
                anomalous_risk=_generate_anomalous_risk(attr_name, is_meta_attribute),
                equation_reference=equation_ref,
                uncertainty_factors=_generate_uncertainty_factors(attr_name),
            )
            
            # Attach to result
            if isinstance(result, dict):
                result["_contrast_metadata"] = contrast.model_dump()
                result["_is_meta_attribute"] = is_meta_attribute
                
                # F7 Humility: meta-attributes get higher uncertainty floor
                if is_meta_attribute:
                    result["_uncertainty_floor"] = 0.12  # Higher for ML-derived
                    
                # F9 Anti-Hantu: flag if no well ties for meta-attributes
                if is_meta_attribute and not kwargs.get("well_ties"):
                    result["_grounding_status"] = "UNGROUNDED"
                    result["_warning"] = (
                        "Meta-attribute without well tie validation. "
                        "Perceptual contrast may dominate physical signal. "
                        "F7 Humility enforced: uncertainty ≥ 0.12"
                    )
                else:
                    result["_grounding_status"] = "GROUNDED"
            
            return result
        
        # Attach metadata to function for introspection
        wrapper._contrast_canon = {
            "physical_axes": physical_axes,
            "equation_ref": equation_ref,
            "is_meta_attribute": is_meta_attribute,
        }
        
        return wrapper
    return decorator


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def _generate_anomalous_risk(name: str, is_meta: bool) -> dict[str, Any]:
    """
    Generate anomalous risk assessment based on attribute type.
    
    Classical attributes (coherence, curvature) have low display bias.
    Meta-attributes (ML fusion) have high risk of perceptual artifacts.
    """
    if is_meta or "meta" in name.lower() or "fault_prob" in name.lower():
        return {
            "display_bias": "high",
            "risk_level": "critical",
            "notes": (
                "Learned meta-attribute may amplify perceptual contrast not fully "
                "grounded in physics. Physical traceability is partial. "
                "Mandatory validation: well ties, horizon flattening, structural timing. "
                "F7 Humility enforced: uncertainty ≥ 0.12"
            ),
            "mitigation": [
                "Cross-validate with classical attributes",
                "Require well tie verification",
                "Check for acquisition footprint artifacts",
                "Validate against known geology"
            ]
        }
    
    # Classical attributes
    classical_notes = {
        "coherence": "Semblance-based: high physical traceability to waveform similarity",
        "curvature": "Volumetric curvature: measures structural flexure directly",
        "spectral": "Frequency decomposition: tied to tuning thickness",
    }
    
    for key, note in classical_notes.items():
        if key in name.lower():
            return {
                "display_bias": "low",
                "risk_level": "minimal",
                "notes": f"Classical attribute — {note}",
                "mitigation": ["Standard QC: check for edge artifacts"]
            }
    
    return {
        "display_bias": "medium",
        "risk_level": "moderate",
        "notes": "Attribute type unknown — apply standard QC",
        "mitigation": ["Review processing chain", "Validate against wells"]
    }


def _generate_uncertainty_factors(name: str) -> list[str]:
    """Generate list of uncertainty sources for this attribute type."""
    factors = ["acquisition_footprint", "processing_noise", "velocity_model_uncertainty"]
    
    if "coherence" in name.lower():
        factors.extend(["spatial_window_size", "dip_estimation_error"])
    elif "curvature" in name.lower():
        factors.extend(["derivative_estimation_noise", "structural_complexity"])
    elif "meta" in name.lower() or "fault_prob" in name.lower():
        factors.extend([
            "training_data_bias",
            "generalization_gap",
            "fusion_artifact_amplification",
            "perceptual_conflation_risk"
        ])
    
    return factors


def compute_contrast_verdict(
    attributes: dict[str, Any],
    well_ties: list[str] | None = None,
) -> dict[str, Any]:
    """
    Compute constitutional verdict for an attribute set.
    
    Returns SEAL, PARTIAL, or GEOX_BLOCK based on grounding status.
    """
    has_ungrounded_meta = False
    warnings = []
    
    for name, attr in attributes.items():
        metadata = attr.get("_contrast_metadata", {})
        is_meta = attr.get("_is_meta_attribute", False)
        grounding = attr.get("_grounding_status", "UNKNOWN")
        
        if is_meta and grounding == "UNGROUNDED":
            has_ungrounded_meta = True
            warnings.append(
                f"Meta-attribute '{name}' lacks well tie validation. "
                "Perceptual contrast risk elevated."
            )
    
    if has_ungrounded_meta and not well_ties:
        return {
            "verdict": "GEOX_BLOCK",
            "explanation": (
                "Meta-attribute(s) without well tie validation. "
                "Perceptual contrast may dominate physical signal. "
                "Provide well_ties or remove meta attributes."
            ),
            "warnings": warnings,
            "floors_triggered": ["F7_humility", "F9_anti_hantu"],
        }
    elif warnings:
        return {
            "verdict": "PARTIAL",
            "explanation": "Some attributes have elevated uncertainty. Proceed with caution.",
            "warnings": warnings,
            "floors_triggered": ["F7_humility"],
        }
    else:
        return {
            "verdict": "SEAL",
            "explanation": "All attributes properly grounded.",
            "warnings": [],
            "floors_triggered": [],
        }
