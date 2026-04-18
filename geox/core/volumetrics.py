"""
Probabilistic Volumetrics — P10/P50/P90 HCPV via Monte Carlo.
DITEMPA BUKAN DIBERI

Computes hydrocarbon pore volume (HCPV) and STOIIP/GIIP using
Monte Carlo simulation (N=10,000 draws) with triangular or lognormal
distributions for each input parameter.

Chain: GRV → NTG → POR → Sw → FVF → HCPV (bbl or bcf)

Constitutional requirement: No deterministic single-value volume output.
If P90/P10 > 5.0 → hold_enforced = True (PhysicsGuard posterior breadth rule).
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

_N_DRAWS = 10_000
_RNG_SEED = 42  # reproducible default; callers may override


@dataclass
class TriangularDist:
    """Triangular distribution defined by (min, most_likely, max)."""
    min_val: float
    ml_val: float    # mode / most likely
    max_val: float

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return rng.triangular(self.min_val, self.ml_val, self.max_val, size=n)


@dataclass
class LognormalDist:
    """Lognormal distribution defined by (P50, std_dev_of_log)."""
    p50: float
    log_std: float = 0.3

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        mu = np.log(self.p50)
        return rng.lognormal(mu, self.log_std, size=n)


# Type alias for distribution inputs
DistInput = TriangularDist | LognormalDist


@dataclass
class VolumeDistribution:
    """Monte Carlo HCPV result with full P10/P50/P90 table."""
    p10: float          # HCPV P10 (bbl or bcf)
    p50: float          # HCPV P50
    p90: float          # HCPV P90
    mean: float
    std_dev: float
    unit: str
    n_draws: int
    n_valid: int        # draws that passed PhysicsGuard
    posterior_ratio: float  # P90 / P10
    hold_enforced: bool
    claim_tag: str
    tornado_data: list[dict[str, Any]]    # per-parameter sensitivity contribution
    vault_receipt: dict[str, Any]
    audit_trace: str
    physics_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "p10": round(self.p10, 4),
            "p50": round(self.p50, 4),
            "p90": round(self.p90, 4),
            "mean": round(self.mean, 4),
            "std_dev": round(self.std_dev, 4),
            "unit": self.unit,
            "n_draws": self.n_draws,
            "n_valid": self.n_valid,
            "posterior_ratio": round(self.posterior_ratio, 4),
            "hold_enforced": self.hold_enforced,
            "claim_tag": self.claim_tag,
            "tornado_data": self.tornado_data,
            "vault_receipt": self.vault_receipt,
            "audit_trace": self.audit_trace,
            "physics_status": self.physics_status,
        }


class ProbabilisticVolumetrics:
    """Monte Carlo HCPV/STOIIP estimation with PhysicsGuard validation.

    Usage::

        vol = ProbabilisticVolumetrics()
        result = vol.compute_hcpv(
            grv_dist=TriangularDist(50, 100, 200),   # km²
            ntg_dist=TriangularDist(0.4, 0.6, 0.8),
            phi_dist=TriangularDist(0.10, 0.18, 0.28),
            sw_dist=TriangularDist(0.20, 0.35, 0.55),
            fvf=1.35,
            unit="MMbbl",
        )
    """

    def __init__(self, n_draws: int = _N_DRAWS) -> None:
        self.n_draws = n_draws

    def compute_hcpv(
        self,
        grv_dist: DistInput,
        ntg_dist: DistInput,
        phi_dist: DistInput,
        sw_dist: DistInput,
        fvf: float,
        unit: str = "MMbbl",
        seed: int | None = _RNG_SEED,
        session_id: str | None = None,
    ) -> VolumeDistribution:
        """Compute probabilistic HCPV via Monte Carlo (N draws).

        Args:
            grv_dist: Gross rock volume distribution (km² or Mm³ — caller's unit)
            ntg_dist: Net-to-gross ratio distribution [0, 1]
            phi_dist: Porosity distribution [0.02, 0.45]
            sw_dist: Water saturation distribution [0, 1]
            fvf: Formation volume factor (bbl/STB or Mcf/scf), deterministic scalar
            unit: Label for output unit string
            seed: RNG seed for reproducibility (None = random)
            session_id: Optional session ID for VAULT999 receipt

        Returns:
            VolumeDistribution with P10/P50/P90 and tornado data.
        """
        rng = np.random.default_rng(seed)

        grv = grv_dist.sample(self.n_draws, rng)
        ntg = ntg_dist.sample(self.n_draws, rng)
        phi = phi_dist.sample(self.n_draws, rng)
        sw = sw_dist.sample(self.n_draws, rng)

        # Clamp to physical bounds before computing
        ntg = np.clip(ntg, 0.0, 1.0)
        phi = np.clip(phi, 0.02, 0.45)
        sw = np.clip(sw, 0.0, 1.0)
        grv = np.clip(grv, 0.0, None)

        # PhysicsGuard: reject draws where Sw or phi are out-of-bounds
        valid_mask = (sw >= 0.0) & (sw <= 1.0) & (phi >= 0.02) & (phi <= 0.45)
        n_valid = int(np.sum(valid_mask))

        grv_v = grv[valid_mask]
        ntg_v = ntg[valid_mask]
        phi_v = phi[valid_mask]
        sw_v = sw[valid_mask]

        if n_valid < 100:
            # Not enough valid draws — return a hold result
            now_ts = datetime.now(timezone.utc).isoformat()
            return VolumeDistribution(
                p10=0.0, p50=0.0, p90=0.0, mean=0.0, std_dev=0.0,
                unit=unit, n_draws=self.n_draws, n_valid=n_valid,
                posterior_ratio=0.0, hold_enforced=True,
                claim_tag=ClaimTag.UNKNOWN.value,
                tornado_data=[],
                vault_receipt={"timestamp": now_ts, "hash": "INVALID", "hold_enforced": True},
                audit_trace=f"INSUFFICIENT_VALID_DRAWS: {n_valid}/{self.n_draws}",
                physics_status="PHYSICS_VIOLATION",
            )

        # HCPV = GRV * NTG * PHI * (1 - Sw) / FVF
        hcpv = grv_v * ntg_v * phi_v * (1.0 - sw_v) / max(fvf, 0.001)

        p10 = float(np.percentile(hcpv, 10))
        p50 = float(np.percentile(hcpv, 50))
        p90 = float(np.percentile(hcpv, 90))
        mean_v = float(np.mean(hcpv))
        std_v = float(np.std(hcpv))

        posterior_ratio = (p90 / p10) if p10 > 0 else 999.0
        breadth_check = _guard.check_posterior_breadth(p10=max(p10, 1e-6), p50=p50, p90=p90)
        hold_enforced = breadth_check.hold

        # Tornado data: variance contribution by parameter
        tornado_data = self._compute_tornado(grv_v, ntg_v, phi_v, sw_v, hcpv)

        # Epistemic tag
        if posterior_ratio <= 2.0 and not hold_enforced:
            claim_tag = ClaimTag.CLAIM.value
        elif posterior_ratio <= 4.0 and not hold_enforced:
            claim_tag = ClaimTag.PLAUSIBLE.value
        elif posterior_ratio <= 5.0:
            claim_tag = ClaimTag.HYPOTHESIS.value
        else:
            claim_tag = ClaimTag.ESTIMATE.value

        # VAULT999 receipt
        ts = datetime.now(timezone.utc).isoformat()
        receipt_payload = f"hcpv|p50={p50:.2f}|ratio={posterior_ratio:.2f}|{ts}"
        vault_receipt = {
            "epoch": int(time.time()),
            "session_id": session_id or "N/A",
            "hash": hashlib.sha256(receipt_payload.encode()).hexdigest()[:16],
            "hold_enforced": hold_enforced,
            "timestamp": ts,
        }

        physics_status = breadth_check.status
        audit_trace = (
            f"n_draws={self.n_draws} n_valid={n_valid} "
            f"| p10={p10:.2f} p50={p50:.2f} p90={p90:.2f} ratio={posterior_ratio:.2f} "
            f"| claim={claim_tag} hold={hold_enforced}"
        )

        return VolumeDistribution(
            p10=round(p10, 4),
            p50=round(p50, 4),
            p90=round(p90, 4),
            mean=round(mean_v, 4),
            std_dev=round(std_v, 4),
            unit=unit,
            n_draws=self.n_draws,
            n_valid=n_valid,
            posterior_ratio=round(posterior_ratio, 4),
            hold_enforced=hold_enforced,
            claim_tag=claim_tag,
            tornado_data=tornado_data,
            vault_receipt=vault_receipt,
            audit_trace=audit_trace,
            physics_status=physics_status,
        )

    @staticmethod
    def _compute_tornado(
        grv: np.ndarray,
        ntg: np.ndarray,
        phi: np.ndarray,
        sw: np.ndarray,
        hcpv: np.ndarray,
    ) -> list[dict[str, Any]]:
        """Compute Spearman correlation of each input with HCPV as a tornado proxy."""
        from scipy.stats import spearmanr  # type: ignore[import-untyped]

        entries = []
        params = [
            ("GRV", grv),
            ("NTG", ntg),
            ("PHI", phi),
            ("Sw", sw),
        ]
        for name, arr in params:
            if len(arr) > 10:
                corr, _ = spearmanr(arr, hcpv)
                entries.append({
                    "parameter": name,
                    "spearman_r": round(float(corr), 4),
                    "abs_impact": round(abs(float(corr)), 4),
                })
        entries.sort(key=lambda x: x["abs_impact"], reverse=True)
        return entries
