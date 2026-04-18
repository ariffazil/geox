"""
Petro Ensemble — Multi-Model Sw Computation Engine.
DITEMPA BUKAN DIBERI

Computes water saturation (Sw) simultaneously using:
  - Archie (1942): Sw = (a * Rw / (phi^m * Rt))^(1/n)
  - Indonesia equation (Poupon & Leveaux 1971)
  - Simandoux (1963)

Returns P10/P50/P90 band across model spread plus epistemic ClaimTag.
If disagreement_band > 0.20 → hold_enforced = True (888_HOLD).
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import numpy as np

from geox.core.ac_risk import ClaimTag
from geox.core.physics_guard import PhysicsGuard

_guard = PhysicsGuard()

# Default Archie cementation/tortuosity constants
_DEFAULT_A = 1.0
_DEFAULT_M = 2.0
_DEFAULT_N = 2.0


def _clamp(value: float, lo: float, hi: float) -> float:
    return float(max(lo, min(hi, value)))


def _archie(rt: float, phi: float, rw: float,
            a: float = _DEFAULT_A, m: float = _DEFAULT_M, n: float = _DEFAULT_N) -> float:
    """Archie (1942) water saturation.

    Sw = (a * Rw / (phi^m * Rt))^(1/n)
    """
    if phi <= 0 or rt <= 0 or rw <= 0:
        return 1.0
    sw = (a * rw / (phi ** m * rt)) ** (1.0 / n)
    return _clamp(sw, 0.0, 1.0)


def _indonesia(rt: float, phi: float, rw: float, vsh: float,
               rsh: float = 4.0,
               a: float = _DEFAULT_A, m: float = _DEFAULT_M, n: float = _DEFAULT_N) -> float:
    """Indonesia equation (Poupon & Leveaux 1971).

    1/sqrt(Rt) = Sw^(n/2) * (phi^(m/2) / sqrt(a * Rw)) + Vsh^(1 - vsh/2) / sqrt(Rsh)
    Solved for Sw numerically.
    """
    if phi <= 0 or rt <= 0 or rw <= 0 or vsh < 0:
        return 1.0
    vsh_c = _clamp(vsh, 0.0, 1.0)
    rsh_c = max(rsh, 0.01)

    conductivity = 1.0 / rt
    shale_term = (vsh_c ** (1.0 - vsh_c / 2.0)) / (rsh_c ** 0.5)
    clean_term = (phi ** (m / 2.0)) / ((a * rw) ** 0.5)

    if clean_term <= 0:
        return 1.0

    # Solve iteratively: f(Sw) = 0
    # 1/sqrt(Rt) = Sw^(n/2) * clean_term + shale_term
    target = (conductivity ** 0.5) - shale_term
    if target <= 0:
        return 1.0

    sw = (target / clean_term) ** (2.0 / n)
    return _clamp(sw, 0.0, 1.0)


def _simandoux(rt: float, phi: float, rw: float, vsh: float,
               rsh: float = 4.0,
               a: float = _DEFAULT_A, m: float = _DEFAULT_M, n: float = _DEFAULT_N) -> float:
    """Simandoux (1963) water saturation.

    Sw = (a * Rw / (2 * phi^m)) * (sqrt((Vsh/Rsh)^2 + 4*phi^m/(a*Rw*Rt)) - Vsh/Rsh)
    """
    if phi <= 0 or rt <= 0 or rw <= 0 or vsh < 0:
        return 1.0
    vsh_c = _clamp(vsh, 0.0, 1.0)
    rsh_c = max(rsh, 0.01)

    phi_m = phi ** m
    numerator_factor = a * rw / (2.0 * phi_m)
    discriminant = (vsh_c / rsh_c) ** 2 + 4.0 * phi_m / (a * rw * rt)
    if discriminant < 0:
        return 1.0

    sw = numerator_factor * (discriminant ** 0.5 - vsh_c / rsh_c)
    return _clamp(sw, 0.0, 1.0)


@dataclass
class EnsembleResult:
    """Result of multi-model Sw ensemble computation."""
    models: dict[str, float]         # {"archie": sw, "indonesia": sw, "simandoux": sw}
    mean: float                       # Arithmetic mean across models
    p10: float                        # 10th percentile of model spread
    p50: float                        # 50th percentile of model spread
    p90: float                        # 90th percentile of model spread
    disagreement_band: float          # P90 - P10
    claim_tag: str
    hold_enforced: bool               # True if band > 0.20
    physics_status: str
    vault_receipt: dict[str, Any]
    audit_trace: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "models": {k: round(v, 4) for k, v in self.models.items()},
            "mean": round(self.mean, 4),
            "p10": round(self.p10, 4),
            "p50": round(self.p50, 4),
            "p90": round(self.p90, 4),
            "disagreement_band": round(self.disagreement_band, 4),
            "claim_tag": self.claim_tag,
            "hold_enforced": self.hold_enforced,
            "physics_status": self.physics_status,
            "vault_receipt": self.vault_receipt,
            "audit_trace": self.audit_trace,
        }


class PetroEnsemble:
    """Multi-model petrophysics ensemble for water saturation estimation.

    All three models are computed simultaneously. The model spread defines
    epistemic uncertainty (disagreement_band = P90 - P10).
    """

    HOLD_THRESHOLD = 0.20
    PLAUSIBLE_THRESHOLD = 0.15

    def __init__(self,
                 a: float = _DEFAULT_A,
                 m: float = _DEFAULT_M,
                 n: float = _DEFAULT_N,
                 rsh: float = 4.0) -> None:
        self.a = a
        self.m = m
        self.n = n
        self.rsh = rsh

    def compute_sw_ensemble(
        self,
        rt: float,
        phi: float,
        rw: float,
        vsh: float,
        temp: float = 25.0,
        session_id: str | None = None,
    ) -> EnsembleResult:
        """Compute Sw from all three models simultaneously.

        Args:
            rt: True resistivity (ohm.m)
            phi: Effective porosity (v/v, e.g. 0.20)
            rw: Formation water resistivity (ohm.m)
            vsh: Shale volume fraction (v/v, e.g. 0.15)
            temp: Reservoir temperature (°C), used for future Rw corrections
            session_id: Optional session identifier for VAULT999 receipt

        Returns:
            EnsembleResult with all three model results and P10/P50/P90 band.
        """
        sw_archie = _archie(rt, phi, rw, self.a, self.m, self.n)
        sw_indonesia = _indonesia(rt, phi, rw, vsh, self.rsh, self.a, self.m, self.n)
        sw_simandoux = _simandoux(rt, phi, rw, vsh, self.rsh, self.a, self.m, self.n)

        values = np.array([sw_archie, sw_indonesia, sw_simandoux])
        p10 = float(np.percentile(values, 10))
        p50 = float(np.percentile(values, 50))
        p90 = float(np.percentile(values, 90))
        mean_sw = float(np.mean(values))
        band = round(p90 - p10, 6)

        # Validate ALL three model outputs through PhysicsGuard
        physics_violations: list[str] = []
        for model_name, sw_val in [("archie", sw_archie), ("indonesia", sw_indonesia), ("simandoux", sw_simandoux)]:
            result = _guard.validate({"sw": sw_val})
            if result.hold:
                physics_violations.append(f"{model_name}:PHYSICS_VIOLATION(sw={sw_val:.4f})")

        physics_status = "PHYSICS_VIOLATION" if physics_violations else "PASS"

        # Epistemic classification
        hold_enforced = band > self.HOLD_THRESHOLD or bool(physics_violations)
        if band <= self.PLAUSIBLE_THRESHOLD and not physics_violations:
            claim_tag = ClaimTag.CLAIM.value
        elif band <= self.HOLD_THRESHOLD and not physics_violations:
            claim_tag = ClaimTag.PLAUSIBLE.value
        elif band <= 0.35:
            claim_tag = ClaimTag.HYPOTHESIS.value
        else:
            claim_tag = ClaimTag.ESTIMATE.value

        # VAULT999 receipt
        ts = datetime.now(timezone.utc).isoformat()
        receipt_payload = f"ensemble_sw|{mean_sw:.4f}|{band:.4f}|{ts}"
        vault_receipt = {
            "epoch": int(time.time()),
            "session_id": session_id or "N/A",
            "hash": hashlib.sha256(receipt_payload.encode()).hexdigest()[:16],
            "hold_enforced": hold_enforced,
            "timestamp": ts,
        }

        audit_trace = (
            f"archie={sw_archie:.4f} indonesia={sw_indonesia:.4f} simandoux={sw_simandoux:.4f} "
            f"| p10={p10:.4f} p50={p50:.4f} p90={p90:.4f} band={band:.4f} "
            f"| claim_tag={claim_tag} hold={hold_enforced}"
        )

        return EnsembleResult(
            models={"archie": sw_archie, "indonesia": sw_indonesia, "simandoux": sw_simandoux},
            mean=round(mean_sw, 6),
            p10=round(p10, 6),
            p50=round(p50, 6),
            p90=round(p90, 6),
            disagreement_band=band,
            claim_tag=claim_tag,
            hold_enforced=hold_enforced,
            physics_status=physics_status,
            vault_receipt=vault_receipt,
            audit_trace=audit_trace,
        )
