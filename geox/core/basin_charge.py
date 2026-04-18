"""
Basin Charge Simulation — TTI + Easy%Ro + Migration Pathway.
DITEMPA BUKAN DIBERI

Implements:
  - TTI (Time-Temperature Index) via Lopatin (1971) method
  - Easy%Ro vitrinite reflectance model (Sweeney & Burnham 1990)
  - Simple Darcy-based migration pathway tracer (buoyancy + carrier bed)
  - Charge risk output: charge_probability, migration_distance_km, seal_integrity_estimate
"""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from geox.core.ac_risk import ClaimTag
from geox.core.physics_guard import PhysicsGuard

_guard = PhysicsGuard()


# ============================================================================
# TTI (Lopatin method)
# ============================================================================

def compute_tti(burial_history: list[dict[str, float]]) -> float:
    """Compute Time-Temperature Index (TTI) via Lopatin (1971).

    Args:
        burial_history: List of dicts, each with:
            - "age_ma_start": Age at start of interval (Ma)
            - "age_ma_end": Age at end of interval (Ma)
            - "temp_start_c": Temperature at start (°C)
            - "temp_end_c": Temperature at end (°C)

    Returns:
        TTI (dimensionless) — higher = more mature.

    TTI formula:
        For each time interval Δt:
            r_i = 2^((T_avg - 105) / 10)
            TTI += Δt * r_i
    """
    tti = 0.0
    for interval in burial_history:
        t_start = float(interval.get("age_ma_start", 0.0))
        t_end = float(interval.get("age_ma_end", 0.0))
        temp_start = float(interval.get("temp_start_c", 25.0))
        temp_end = float(interval.get("temp_end_c", 25.0))

        delta_t = abs(t_start - t_end)          # Myr
        t_avg = (temp_start + temp_end) / 2.0   # °C

        r_i = 2.0 ** ((t_avg - 105.0) / 10.0)
        tti += delta_t * r_i

    return round(tti, 4)


# ============================================================================
# Easy%Ro (Sweeney & Burnham 1990)
# ============================================================================

# Activation energies (kcal/mol) and frequency factor
_EASY_RO_E = [
    34, 36, 38, 40, 42, 44, 46, 48, 50, 52,
    54, 56, 58, 60, 62, 64, 66, 68, 70, 72,
]
_EASY_RO_F = [
    0.03, 0.03, 0.04, 0.04, 0.05, 0.05, 0.06, 0.04, 0.04, 0.07,
    0.06, 0.06, 0.06, 0.05, 0.05, 0.04, 0.03, 0.02, 0.02, 0.01,
]
_EASY_RO_A = 1.0e13  # frequency factor (s^-1)
_R = 1.987e-3        # gas constant (kcal/mol/K)


def compute_easy_ro(burial_history: list[dict[str, float]]) -> float:
    """Compute Easy%Ro vitrinite reflectance via Sweeney & Burnham (1990).

    Args:
        burial_history: Same format as compute_tti. Each interval must have
            "age_ma_start", "age_ma_end", "temp_start_c", "temp_end_c".

    Returns:
        %Ro (vitrinite reflectance, %) — typical oil window: 0.6–1.3%
    """
    # Compute fraction of each reaction that has reacted
    f_reacted = [0.0] * len(_EASY_RO_E)

    for interval in burial_history:
        t_start = float(interval.get("age_ma_start", 0.0))
        t_end = float(interval.get("age_ma_end", 0.0))
        temp_start = float(interval.get("temp_start_c", 25.0))
        temp_end = float(interval.get("temp_end_c", 25.0))

        delta_t_sec = abs(t_start - t_end) * 1e6 * 365.25 * 24.0 * 3600.0
        t_avg_k = (temp_start + temp_end) / 2.0 + 273.15

        for i, (e, _f) in enumerate(zip(_EASY_RO_E, _EASY_RO_F)):
            k = _EASY_RO_A * math.exp(-e / (_R * t_avg_k))
            f_reacted[i] = min(1.0, f_reacted[i] + k * delta_t_sec)

    # Transformation ratio F
    f_total = sum(_EASY_RO_F[i] * f_reacted[i] for i in range(len(_EASY_RO_E)))
    f_total = min(max(f_total, 0.0), 1.0)

    # Convert to %Ro: ln(Ro) = -1.6 + 3.7 * F
    ro_ln = -1.6 + 3.7 * f_total
    ro = math.exp(ro_ln)
    return round(ro, 4)


# ============================================================================
# Migration Pathway Tracer (Darcy buoyancy)
# ============================================================================

def compute_migration_distance(
    carrier_permeability_md: float,
    carrier_thickness_m: float,
    buoyancy_gradient_mpa_per_km: float,
    viscosity_cp: float = 1.0,
    migration_time_ma: float = 5.0,
) -> float:
    """Estimate migration distance via Darcy flow in carrier bed.

    Uses simplified Darcy: Q = k * A * ΔP / (μ * L)
    Solved for L given migration time.

    Args:
        carrier_permeability_md: Carrier bed permeability (millidarcies)
        carrier_thickness_m: Carrier bed thickness (m)
        buoyancy_gradient_mpa_per_km: Buoyancy pressure gradient (MPa/km)
        viscosity_cp: Oil/gas viscosity (cP)
        migration_time_ma: Available migration time (Ma)

    Returns:
        Estimated migration distance (km).
    """
    if carrier_permeability_md <= 0 or carrier_thickness_m <= 0:
        return 0.0

    k_m2 = carrier_permeability_md * 9.869e-16        # md → m²
    delta_p_pa_per_m = buoyancy_gradient_mpa_per_km * 1e6 / 1e3  # MPa/km → Pa/m
    mu_pa_s = viscosity_cp * 1e-3                      # cP → Pa·s
    t_sec = migration_time_ma * 1e6 * 365.25 * 24.0 * 3600.0

    if mu_pa_s <= 0 or delta_p_pa_per_m <= 0:
        return 0.0

    # Darcy velocity (m/s): v = k * ΔP/μ (per unit length → need iterative)
    # Simplified: distance = sqrt(2 * k * ΔP * t / μ) — from diffusion analog
    dist_m = math.sqrt(2.0 * k_m2 * delta_p_pa_per_m * t_sec / mu_pa_s)
    return round(dist_m / 1000.0, 3)   # convert to km


# ============================================================================
# Charge Risk Output
# ============================================================================

@dataclass
class ChargeResult:
    """Integrated basin charge simulation result."""
    tti: float
    easy_ro: float
    maturity_window: str           # "IMMATURE" | "OIL_WINDOW" | "GAS_WINDOW" | "OVERMATURE"
    charge_probability: float      # 0.0–1.0
    migration_distance_km: float
    seal_integrity_estimate: float  # 0.0–1.0
    hold_enforced: bool
    claim_tag: str
    physics_status: str
    vault_receipt: dict[str, Any]
    audit_trace: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "tti": self.tti,
            "easy_ro": self.easy_ro,
            "maturity_window": self.maturity_window,
            "charge_probability": round(self.charge_probability, 4),
            "migration_distance_km": round(self.migration_distance_km, 3),
            "seal_integrity_estimate": round(self.seal_integrity_estimate, 4),
            "hold_enforced": self.hold_enforced,
            "claim_tag": self.claim_tag,
            "physics_status": self.physics_status,
            "vault_receipt": self.vault_receipt,
            "audit_trace": self.audit_trace,
        }


def _classify_maturity(ro: float) -> str:
    if ro < 0.6:
        return "IMMATURE"
    elif ro <= 1.3:
        return "OIL_WINDOW"
    elif ro <= 3.0:
        return "GAS_WINDOW"
    else:
        return "OVERMATURE"


def _charge_probability_from_ro(ro: float, tti: float) -> float:
    """Heuristic charge probability based on Ro and TTI.

    Oil window (0.6–1.3%): probability peaks at Ro=0.9.
    Gas window (1.3–3.0%): lower probability (residual/dry gas).
    Immature or overmature: low probability.
    """
    if ro < 0.6:
        prob = min(ro / 0.6 * 0.3, 0.3)
    elif ro <= 0.9:
        prob = 0.3 + (ro - 0.6) / 0.3 * 0.5
    elif ro <= 1.3:
        prob = 0.8 - (ro - 0.9) / 0.4 * 0.3
    elif ro <= 3.0:
        prob = 0.5 - (ro - 1.3) / 1.7 * 0.35
    else:
        prob = 0.10

    # Boost slightly if TTI is in confirmed generative range (50–1500)
    if 50 <= tti <= 1500:
        prob = min(prob * 1.1, 1.0)

    return round(float(prob), 4)


class BasinCharge:
    """Basin charge simulation engine.

    Computes TTI, Easy%Ro, migration distance, and charge probability from
    burial history and carrier geometry inputs.
    """

    def simulate(
        self,
        burial_history: list[dict[str, float]],
        carrier_permeability_md: float = 100.0,
        carrier_thickness_m: float = 20.0,
        buoyancy_gradient_mpa_per_km: float = 3.5,
        viscosity_cp: float = 1.0,
        migration_time_ma: float = 5.0,
        seal_rock_thickness_m: float = 50.0,
        seal_permeability_md: float = 0.001,
        session_id: str | None = None,
    ) -> ChargeResult:
        """Run full basin charge simulation.

        Args:
            burial_history: List of burial intervals (age_ma_start, age_ma_end,
                temp_start_c, temp_end_c).
            carrier_permeability_md: Carrier bed permeability (md).
            carrier_thickness_m: Carrier bed thickness (m).
            buoyancy_gradient_mpa_per_km: Buoyancy pressure gradient (MPa/km).
            viscosity_cp: Fluid viscosity (cP).
            migration_time_ma: Available migration time (Ma).
            seal_rock_thickness_m: Seal rock thickness (m) — higher = better seal.
            seal_permeability_md: Seal permeability (md) — lower = better seal.
            session_id: Optional session ID for VAULT999 receipt.

        Returns:
            ChargeResult with TTI, Easy%Ro, charge_probability, migration_distance_km,
            seal_integrity_estimate.
        """
        tti = compute_tti(burial_history)
        easy_ro = compute_easy_ro(burial_history)
        maturity_window = _classify_maturity(easy_ro)
        charge_probability = _charge_probability_from_ro(easy_ro, tti)
        migration_km = compute_migration_distance(
            carrier_permeability_md, carrier_thickness_m,
            buoyancy_gradient_mpa_per_km, viscosity_cp, migration_time_ma,
        )

        # Seal integrity: higher thickness + lower permeability = better seal
        # Simple normalized score [0, 1]
        seal_score = min(1.0, (seal_rock_thickness_m / 100.0) * (1.0 / (1.0 + seal_permeability_md * 100.0)))

        # Validate Ro against PhysicsGuard Ro bounds
        phys_result = _guard.validate({"ro": easy_ro})
        physics_status = phys_result.status
        hold_enforced = phys_result.hold

        # Epistemic tag
        if charge_probability >= 0.6 and not hold_enforced:
            claim_tag = ClaimTag.PLAUSIBLE.value
        elif charge_probability >= 0.3:
            claim_tag = ClaimTag.HYPOTHESIS.value
        else:
            claim_tag = ClaimTag.ESTIMATE.value

        # VAULT999 receipt
        ts = datetime.now(timezone.utc).isoformat()
        receipt_payload = f"basin_charge|ro={easy_ro:.4f}|tti={tti:.2f}|prob={charge_probability:.4f}|{ts}"
        vault_receipt = {
            "epoch": int(time.time()),
            "session_id": session_id or "N/A",
            "hash": hashlib.sha256(receipt_payload.encode()).hexdigest()[:16],
            "hold_enforced": hold_enforced,
            "timestamp": ts,
        }

        audit_trace = (
            f"tti={tti} easy_ro={easy_ro}% maturity={maturity_window} "
            f"| charge_prob={charge_probability} migration_km={migration_km} "
            f"| seal_score={seal_score:.4f} hold={hold_enforced}"
        )

        return ChargeResult(
            tti=tti,
            easy_ro=easy_ro,
            maturity_window=maturity_window,
            charge_probability=charge_probability,
            migration_distance_km=migration_km,
            seal_integrity_estimate=round(seal_score, 4),
            hold_enforced=hold_enforced,
            claim_tag=claim_tag,
            physics_status=physics_status,
            vault_receipt=vault_receipt,
            audit_trace=audit_trace,
        )
