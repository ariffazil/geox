"""
Sensitivity Sweep — One-At-a-Time (OAT) AC_Risk Sensitivity Analysis.
DITEMPA BUKAN DIBERI

Varies each AC_Risk input parameter ±20% while holding all others constant.
Computes Sensitivity Index (SI = ΔScore / ΔInput%) for each parameter.
Ranks inputs by SI and emits tornado chart data.

Constitutional rule:
  If top SI > 0.4 → CRITICAL_SENSITIVITY → verdict demoted from SEAL to PARTIAL.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from geox.core.ac_risk import ClaimTag, compute_ac_risk_governed

_SWEEP_PCT = 0.20   # ±20% perturbation
_CRITICAL_SI = 0.40  # threshold for CRITICAL_SENSITIVITY


@dataclass
class SensitivityEntry:
    """Result for a single parameter OAT sweep."""
    parameter: str
    base_value: float
    low_value: float
    high_value: float
    score_base: float
    score_low: float
    score_high: float
    delta_score_low: float
    delta_score_high: float
    sensitivity_index: float     # SI = max(|Δscore_low|, |Δscore_high|) / sweep_pct
    rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter": self.parameter,
            "base_value": round(self.base_value, 4),
            "low_value": round(self.low_value, 4),
            "high_value": round(self.high_value, 4),
            "score_base": round(self.score_base, 4),
            "score_low": round(self.score_low, 4),
            "score_high": round(self.score_high, 4),
            "delta_score_low": round(self.delta_score_low, 4),
            "delta_score_high": round(self.delta_score_high, 4),
            "sensitivity_index": round(self.sensitivity_index, 4),
            "rank": self.rank,
        }


@dataclass
class SweepResult:
    """Full OAT sensitivity sweep result."""
    base_score: float
    base_verdict: str
    entries: list[SensitivityEntry]
    top_parameter: str
    top_si: float
    critical_sensitivity: bool
    demoted_verdict: str       # "SEAL" → "PARTIAL" if critical
    claim_tag: str
    vault_receipt: dict[str, Any]
    audit_trace: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_score": round(self.base_score, 4),
            "base_verdict": self.base_verdict,
            "entries": [e.to_dict() for e in self.entries],
            "top_parameter": self.top_parameter,
            "top_si": round(self.top_si, 4),
            "critical_sensitivity": self.critical_sensitivity,
            "demoted_verdict": self.demoted_verdict,
            "claim_tag": self.claim_tag,
            "vault_receipt": self.vault_receipt,
            "audit_trace": self.audit_trace,
        }


def _clamp(val: float, lo: float, hi: float) -> float:
    return float(max(lo, min(hi, val)))


def _ac_score(
    u_ambiguity: float,
    evidence_credit: float,
    echo_score: float,
    truth_score: float,
) -> float:
    """Compute AC_Risk score using governed engine."""
    result = compute_ac_risk_governed(
        u_ambiguity=u_ambiguity,
        transform_stack=[],
        evidence_credit=evidence_credit,
        echo_score=echo_score,
        truth_score=truth_score,
        amanah_locked=True,
    )
    return result.ac_risk_score


class SensitivitySweep:
    """One-At-a-Time (OAT) sensitivity analysis for AC_Risk inputs.

    Sweeps each input parameter ±20% from the base case.
    Computes Sensitivity Index (SI) per parameter.
    Ranks parameters by SI for tornado chart rendering.
    """

    def run(
        self,
        u_ambiguity: float,
        evidence_credit: float,
        echo_score: float,
        truth_score: float,
        session_id: str | None = None,
    ) -> SweepResult:
        """Run OAT sensitivity sweep across all four AC_Risk inputs.

        Args:
            u_ambiguity: Physical ambiguity [0.0, 1.0]
            evidence_credit: Evidence grounding score [0.0, 1.0]
            echo_score: Consistency with prior knowledge [0.0, 1.0]
            truth_score: Factual accuracy [0.0, 1.0]
            session_id: Optional session ID for VAULT999 receipt.

        Returns:
            SweepResult with ranked sensitivity entries and tornado data.
        """
        base_score = _ac_score(u_ambiguity, evidence_credit, echo_score, truth_score)
        base_verdict = self._score_to_verdict(base_score)

        params: dict[str, tuple[float, float, float]] = {
            "u_ambiguity": (u_ambiguity, 0.0, 1.0),
            "evidence_credit": (evidence_credit, 0.0, 1.0),
            "echo_score": (echo_score, 0.0, 1.0),
            "truth_score": (truth_score, 0.0, 1.0),
        }

        entries: list[SensitivityEntry] = []
        for param, (base_val, lo, hi) in params.items():
            delta = base_val * _SWEEP_PCT
            low_val = _clamp(base_val - delta, lo, hi)
            high_val = _clamp(base_val + delta, lo, hi)

            kwargs = {
                "u_ambiguity": u_ambiguity,
                "evidence_credit": evidence_credit,
                "echo_score": echo_score,
                "truth_score": truth_score,
            }

            kwargs[param] = low_val
            score_low = _ac_score(**kwargs)  # type: ignore[arg-type]

            kwargs[param] = high_val
            score_high = _ac_score(**kwargs)  # type: ignore[arg-type]

            delta_low = score_low - base_score
            delta_high = score_high - base_score
            si = max(abs(delta_low), abs(delta_high)) / _SWEEP_PCT if _SWEEP_PCT > 0 else 0.0

            entries.append(SensitivityEntry(
                parameter=param,
                base_value=base_val,
                low_value=low_val,
                high_value=high_val,
                score_base=base_score,
                score_low=score_low,
                score_high=score_high,
                delta_score_low=delta_low,
                delta_score_high=delta_high,
                sensitivity_index=round(si, 6),
            ))

        # Rank by SI descending
        entries.sort(key=lambda e: e.sensitivity_index, reverse=True)
        for i, entry in enumerate(entries):
            entry.rank = i + 1

        top = entries[0] if entries else None
        top_si = top.sensitivity_index if top else 0.0
        top_param = top.parameter if top else "N/A"
        critical = top_si > _CRITICAL_SI

        demoted_verdict = "PARTIAL" if critical and base_verdict == "PROCEED" else base_verdict

        claim_tag = ClaimTag.PLAUSIBLE.value if not critical else ClaimTag.HYPOTHESIS.value

        ts = datetime.now(timezone.utc).isoformat()
        receipt_payload = f"sensitivity|top_si={top_si:.4f}|base={base_score:.4f}|{ts}"
        vault_receipt = {
            "epoch": int(time.time()),
            "session_id": session_id or "N/A",
            "hash": hashlib.sha256(receipt_payload.encode()).hexdigest()[:16],
            "critical_sensitivity": critical,
            "timestamp": ts,
        }

        audit_trace = (
            f"base_score={base_score:.4f} verdict={base_verdict} "
            f"| top_param={top_param} top_si={top_si:.4f} critical={critical} "
            f"| demoted_verdict={demoted_verdict}"
        )

        return SweepResult(
            base_score=round(base_score, 6),
            base_verdict=base_verdict,
            entries=entries,
            top_parameter=top_param,
            top_si=round(top_si, 6),
            critical_sensitivity=critical,
            demoted_verdict=demoted_verdict,
            claim_tag=claim_tag,
            vault_receipt=vault_receipt,
            audit_trace=audit_trace,
        )

    @staticmethod
    def _score_to_verdict(score: float) -> str:
        if score < 0.15:
            return "PROCEED"
        elif score < 0.75:
            return "HOLD"
        else:
            return "BLOCK"
