"""
MCP Tool: geox_run_sensitivity_sweep
DITEMPA BUKAN DIBERI

Runs One-At-a-Time (OAT) sensitivity sweep across AC_Risk inputs ±20%.
Computes Sensitivity Index (SI) per parameter and ranks for tornado chart.
If top SI > 0.4 → CRITICAL_SENSITIVITY → verdict demoted to PARTIAL.
"""

from __future__ import annotations

from typing import Any

from geox.core.sensitivity import SensitivitySweep

_sweep = SensitivitySweep()


def geox_run_sensitivity_sweep(
    u_ambiguity: float,
    evidence_credit: float,
    echo_score: float,
    truth_score: float,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Run OAT sensitivity sweep on AC_Risk inputs.

    Each input is varied ±20% from its base value while all others are held
    constant. The Sensitivity Index (SI) = ΔScore / ΔInput% is computed
    per parameter. Parameters are ranked by SI for tornado chart rendering.

    Args:
        u_ambiguity: Physical ambiguity [0.0, 1.0]
        evidence_credit: Evidence grounding score [0.0, 1.0]
        echo_score: Consistency with prior knowledge [0.0, 1.0]
        truth_score: Factual accuracy [0.0, 1.0]
        session_id: Optional session ID for VAULT999 receipt

    Returns:
        Dict with base_score, base_verdict, entries (ranked by SI),
        top_parameter, top_si, critical_sensitivity, demoted_verdict,
        claim_tag, vault_receipt, audit_trace.
    """
    result = _sweep.run(
        u_ambiguity=u_ambiguity,
        evidence_credit=evidence_credit,
        echo_score=echo_score,
        truth_score=truth_score,
        session_id=session_id,
    )
    return result.to_dict()
