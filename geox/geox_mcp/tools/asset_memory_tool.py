"""
MCP Tools: geox_memory_store_asset + geox_memory_recall_asset
DITEMPA BUKAN DIBERI

Cross-domain per-asset memory persistence for field learning.
Memory writes require F11 auth (amanah_locked=True).
Memory reads emit F2 truth-tagged ClaimTag.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from geox.services.asset_memory import AssetMemoryStore

_store: AssetMemoryStore | None = None


def _get_store() -> AssetMemoryStore:
    global _store
    if _store is None:
        _store = AssetMemoryStore()
    return _store


def geox_memory_store_asset(
    asset_id: str,
    eval_type: str,
    payload: dict[str, Any],
    amanah_locked: bool = False,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Store an evaluation result for an asset.

    F11 constitutional requirement: amanah_locked must be True to write.

    Args:
        asset_id: Field/block/well identifier (e.g. "DULANG-A").
        eval_type: Evaluation type (e.g. "petro_ensemble", "volumetrics",
            "basin_charge", "sensitivity", "las_ingest").
        payload: JSON-serializable dict containing the evaluation result.
        amanah_locked: F11 auth flag. Set True only when operator has
            confirmed the write action is sanctioned.
        session_id: Optional session ID for VAULT999 receipt.

    Returns:
        Dict with success, record_id, claim_tag, vault_receipt, audit_trace.
    """
    result = _get_store().store(
        asset_id=asset_id,
        eval_type=eval_type,
        payload=payload,
        amanah_locked=amanah_locked,
        session_id=session_id,
    )
    return result.to_dict()


def geox_memory_recall_asset(
    asset_id: str,
    eval_type: str | None = None,
    limit: int = 20,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Recall stored evaluations for an asset.

    Memory read is F2 truth-tagged (ClaimTag emitted based on record freshness).

    Args:
        asset_id: Field/block/well identifier.
        eval_type: Optional filter by evaluation type. If None, returns all types.
        limit: Maximum number of records to return (default 20).
        session_id: Optional session ID for VAULT999 receipt.

    Returns:
        Dict with n_records, records (list of stored evaluations),
        claim_tag, vault_receipt, audit_trace.
    """
    result = _get_store().recall(
        asset_id=asset_id,
        eval_type=eval_type,
        limit=limit,
        session_id=session_id,
    )
    return result.to_dict()
