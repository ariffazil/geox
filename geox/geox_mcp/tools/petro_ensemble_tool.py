"""
MCP Tool: geox_compute_sw_ensemble
DITEMPA BUKAN DIBERI

Computes Sw simultaneously using Archie, Indonesia, and Simandoux models.
Returns P10/P50/P90 disagreement band and VAULT999 receipt.
If disagreement_band > 0.20 → hold_enforced = True (888_HOLD).
"""

from __future__ import annotations

from typing import Any

from geox.core.petro_ensemble import PetroEnsemble

_ensemble = PetroEnsemble()


def geox_compute_sw_ensemble(
    rt: float,
    phi: float,
    rw: float,
    vsh: float,
    temp: float = 25.0,
    a: float = 1.0,
    m: float = 2.0,
    n: float = 2.0,
    rsh: float = 4.0,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Compute water saturation ensemble using Archie + Indonesia + Simandoux simultaneously.

    Args:
        rt: True resistivity (ohm.m)
        phi: Effective porosity (v/v, e.g. 0.20)
        rw: Formation water resistivity (ohm.m)
        vsh: Shale volume fraction (v/v, e.g. 0.15)
        temp: Reservoir temperature (°C), default 25
        a: Archie tortuosity factor, default 1.0
        m: Archie cementation exponent, default 2.0
        n: Archie saturation exponent, default 2.0
        rsh: Shale resistivity (ohm.m) for shaly-sand models, default 4.0
        session_id: Optional session ID for VAULT999 receipt

    Returns:
        Dict with models, P10/P50/P90, disagreement_band, claim_tag,
        hold_enforced, vault_receipt, audit_trace.
    """
    ensemble = PetroEnsemble(a=a, m=m, n=n, rsh=rsh)
    result = ensemble.compute_sw_ensemble(rt=rt, phi=phi, rw=rw, vsh=vsh, temp=temp, session_id=session_id)
    return result.to_dict()
