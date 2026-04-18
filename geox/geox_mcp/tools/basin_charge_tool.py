"""
MCP Tool: geox_simulate_basin_charge
DITEMPA BUKAN DIBERI

Simulates basin charge using TTI (Lopatin), Easy%Ro (Sweeney & Burnham 1990),
and Darcy-based migration pathway tracer.
Returns charge_probability, migration_distance_km, seal_integrity_estimate.
"""

from __future__ import annotations

from typing import Any

from geox.core.basin_charge import BasinCharge

_charge = BasinCharge()


def geox_simulate_basin_charge(
    burial_history: list[dict[str, float]],
    carrier_permeability_md: float = 100.0,
    carrier_thickness_m: float = 20.0,
    buoyancy_gradient_mpa_per_km: float = 3.5,
    viscosity_cp: float = 1.0,
    migration_time_ma: float = 5.0,
    seal_rock_thickness_m: float = 50.0,
    seal_permeability_md: float = 0.001,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Simulate basin charge: TTI + Easy%Ro + migration pathway.

    Args:
        burial_history: List of burial intervals, each with:
            - age_ma_start: Age at interval start (Ma before present)
            - age_ma_end: Age at interval end (Ma before present)
            - temp_start_c: Temperature at start (°C)
            - temp_end_c: Temperature at end (°C)
        carrier_permeability_md: Carrier bed permeability (md), default 100
        carrier_thickness_m: Carrier bed thickness (m), default 20
        buoyancy_gradient_mpa_per_km: Buoyancy pressure gradient (MPa/km), default 3.5
        viscosity_cp: Fluid viscosity (cP), default 1.0
        migration_time_ma: Available migration time (Ma), default 5.0
        seal_rock_thickness_m: Seal rock thickness (m), default 50
        seal_permeability_md: Seal permeability (md), default 0.001
        session_id: Optional session ID for VAULT999 receipt

    Returns:
        Dict with tti, easy_ro, maturity_window, charge_probability,
        migration_distance_km, seal_integrity_estimate, hold_enforced,
        claim_tag, vault_receipt, audit_trace.
    """
    result = _charge.simulate(
        burial_history=burial_history,
        carrier_permeability_md=carrier_permeability_md,
        carrier_thickness_m=carrier_thickness_m,
        buoyancy_gradient_mpa_per_km=buoyancy_gradient_mpa_per_km,
        viscosity_cp=viscosity_cp,
        migration_time_ma=migration_time_ma,
        seal_rock_thickness_m=seal_rock_thickness_m,
        seal_permeability_md=seal_permeability_md,
        session_id=session_id,
    )
    return result.to_dict()
