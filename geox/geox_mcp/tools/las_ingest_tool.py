"""
MCP Tool: geox_ingest_las
DITEMPA BUKAN DIBERI

Parses a real LAS 2.0/3.0 file using lasio.
Returns LASManifest with curve QC flags, depth range, asset_id, VAULT999 receipt.
"""

from __future__ import annotations

from typing import Any

from geox.services.las_ingestor import LASIngestor

_ingestor = LASIngestor()


def geox_ingest_las(
    filepath: str,
    asset_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Parse and QC a LAS file, returning a LASManifest.

    Args:
        filepath: Absolute path to a .las file (LAS 2.0 or 3.0).
        asset_id: Optional asset/field identifier. Defaults to well name from header.
        session_id: Optional session ID for VAULT999 receipt.

    Returns:
        Dict with asset_id, well_name, uwi, depth_range_m, n_curves,
        curves (per-curve QC), overall_qc_pass, claim_tag, vault_receipt,
        audit_trace.

    Raises:
        FileNotFoundError: If filepath does not exist.
        ValueError: If no depth curve found in the LAS file.
    """
    try:
        manifest = _ingestor.ingest(filepath=filepath, asset_id=asset_id, session_id=session_id)
        return manifest.to_dict()
    except (FileNotFoundError, ValueError) as exc:
        return {
            "error": str(exc),
            "claim_tag": "UNKNOWN",
            "hold_enforced": True,
            "vault_receipt": {"hash": "ERROR", "hold_enforced": True},
            "audit_trace": f"LAS_INGEST_ERROR: {exc}",
        }
