"""
MCP Tool: geox_compute_volume_probabilistic
DITEMPA BUKAN DIBERI

Computes probabilistic HCPV/STOIIP via Monte Carlo (N=10,000).
Accepts triangular or lognormal distributions for GRV, NTG, PHI, Sw, FVF.
Returns P10/P50/P90 table + tornado chart data + VAULT999 seal.
"""

from __future__ import annotations

from typing import Any, Literal

from geox.core.volumetrics import ProbabilisticVolumetrics, TriangularDist, LognormalDist

_vol = ProbabilisticVolumetrics()


def _build_dist(
    dist_type: Literal["triangular", "lognormal"],
    params: dict[str, float],
    name: str,
) -> TriangularDist | LognormalDist:
    if dist_type == "lognormal":
        p50 = params.get("p50", params.get("ml", 1.0))
        log_std = params.get("log_std", 0.3)
        return LognormalDist(p50=p50, log_std=log_std)
    else:
        mn = params.get("min", params.get("min_val", 0.0))
        ml = params.get("ml", params.get("ml_val", params.get("p50", 1.0)))
        mx = params.get("max", params.get("max_val", 2.0))
        return TriangularDist(min_val=mn, ml_val=ml, max_val=mx)


def geox_compute_volume_probabilistic(
    grv_min: float,
    grv_ml: float,
    grv_max: float,
    ntg_min: float,
    ntg_ml: float,
    ntg_max: float,
    phi_min: float,
    phi_ml: float,
    phi_max: float,
    sw_min: float,
    sw_ml: float,
    sw_max: float,
    fvf: float = 1.35,
    unit: str = "MMbbl",
    n_draws: int = 10000,
    seed: int = 42,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Compute probabilistic HCPV/STOIIP via Monte Carlo.

    All four input distributions use triangular (min/ml/max) specification.

    Args:
        grv_min/ml/max: Gross Rock Volume distribution bounds (km² or user unit)
        ntg_min/ml/max: Net-to-gross ratio distribution [0, 1]
        phi_min/ml/max: Porosity distribution [0.02, 0.45]
        sw_min/ml/max: Water saturation distribution [0, 1]
        fvf: Formation volume factor (scalar, e.g. 1.35 bbl/STB)
        unit: Output unit label (default "MMbbl")
        n_draws: Monte Carlo draw count (default 10,000)
        seed: RNG seed for reproducibility (default 42)
        session_id: Optional session ID for VAULT999 receipt

    Returns:
        Dict with p10, p50, p90, mean, std_dev, posterior_ratio,
        hold_enforced, claim_tag, tornado_data, vault_receipt, audit_trace.
    """
    vol = ProbabilisticVolumetrics(n_draws=n_draws)
    result = vol.compute_hcpv(
        grv_dist=TriangularDist(grv_min, grv_ml, grv_max),
        ntg_dist=TriangularDist(ntg_min, ntg_ml, ntg_max),
        phi_dist=TriangularDist(phi_min, phi_ml, phi_max),
        sw_dist=TriangularDist(sw_min, sw_ml, sw_max),
        fvf=fvf,
        unit=unit,
        seed=seed,
        session_id=session_id,
    )
    return result.to_dict()
