"""
MCP Tools: geox_render_log_track + geox_render_volume_slice
DITEMPA BUKAN DIBERI

Visualization tools that return JSON-serializable render payloads
ready for WebGL/Three.js consumer (log track viewer + volume renderer).
Every call emits ClaimTag + VAULT999 receipt.
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from typing import Any

import numpy as np

from geox.core.ac_risk import ClaimTag


def _make_vault(tag: str, session_id: str | None) -> dict[str, Any]:
    ts = datetime.now(timezone.utc).isoformat()
    h = hashlib.sha256(f"{tag}|{ts}".encode()).hexdigest()[:16]
    return {
        "epoch": int(time.time()),
        "session_id": session_id or "N/A",
        "hash": h,
        "timestamp": ts,
    }


def geox_render_log_track(
    depth: list[float],
    gr: list[float] | None = None,
    rhob: list[float] | None = None,
    nphi: list[float] | None = None,
    rt: list[float] | None = None,
    track_width_px: int = 80,
    depth_unit: str = "m",
    session_id: str | None = None,
) -> dict[str, Any]:
    """Prepare a log track render payload for WebGL canvas.

    Returns normalised curve arrays (0–1 scale) with track metadata
    ready for a LogTrackViewer WebGL consumer. Every curve is normalised
    to its physical display range.

    Args:
        depth: Depth array (m or ft).
        gr: Gamma Ray (gAPI), display range 0–150.
        rhob: Bulk Density (g/cc), display range 1.8–2.95 (reversed).
        nphi: Neutron Porosity (v/v), display range 0.45–(-0.05) (reversed).
        rt: Resistivity (ohm.m), log scale 0.1–1000.
        track_width_px: Width per track panel (default 80 px).
        depth_unit: Depth unit label.
        session_id: Optional session ID for VAULT999 receipt.

    Returns:
        Dict with tracks (normalised arrays + metadata) + vault_receipt.
    """
    import math

    def _norm(arr: list[float] | None, lo: float, hi: float, log_scale: bool = False) -> list[float] | None:
        if arr is None:
            return None
        result = []
        for v in arr:
            if v is None or (isinstance(v, float) and math.isnan(v)):
                result.append(None)  # type: ignore[arg-type]
                continue
            if log_scale:
                lo_l = math.log10(max(lo, 1e-9))
                hi_l = math.log10(max(hi, 1e-9))
                v_l = math.log10(max(v, 1e-9))
                result.append(round((v_l - lo_l) / max(hi_l - lo_l, 1e-9), 6))
            else:
                result.append(round((v - lo) / max(hi - lo, 1e-9), 6))
        return result

    tracks: list[dict[str, Any]] = []

    if gr is not None:
        tracks.append({
            "mnemonic": "GR",
            "unit": "gAPI",
            "display_range": [0, 150],
            "fill_color": "#7CFC00",
            "log_scale": False,
            "width_px": track_width_px,
            "normalised": _norm(gr, 0.0, 150.0),
        })

    if rhob is not None:
        tracks.append({
            "mnemonic": "RHOB",
            "unit": "g/cc",
            "display_range": [2.95, 1.8],  # reversed for petrophysics convention
            "fill_color": "#FF6347",
            "log_scale": False,
            "width_px": track_width_px,
            "normalised": _norm(rhob, 1.8, 2.95),
        })

    if nphi is not None:
        tracks.append({
            "mnemonic": "NPHI",
            "unit": "v/v",
            "display_range": [0.45, -0.05],  # reversed
            "fill_color": "#4169E1",
            "log_scale": False,
            "width_px": track_width_px,
            "normalised": _norm(nphi, -0.05, 0.45),
        })

    if rt is not None:
        tracks.append({
            "mnemonic": "RT",
            "unit": "ohm.m",
            "display_range": [0.1, 1000.0],
            "fill_color": "#FFD700",
            "log_scale": True,
            "width_px": track_width_px,
            "normalised": _norm(rt, 0.1, 1000.0, log_scale=True),
        })

    vault_receipt = _make_vault("render_log_track", session_id)

    return {
        "render_type": "log_track",
        "depth": depth,
        "depth_unit": depth_unit,
        "n_samples": len(depth),
        "tracks": tracks,
        "track_width_px": track_width_px,
        "claim_tag": ClaimTag.CLAIM.value,
        "vault_receipt": vault_receipt,
        "audit_trace": f"log_track|tracks={[t['mnemonic'] for t in tracks]}|n={len(depth)}",
    }


def geox_render_volume_slice(
    volume_data: list[list[float]],
    slice_axis: str = "z",
    slice_index: int = 0,
    nx: int | None = None,
    ny: int | None = None,
    attribute_name: str = "amplitude",
    colormap: str = "seismic",
    vmin: float | None = None,
    vmax: float | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Prepare a 2D volume slice render payload for WebGL canvas.

    Args:
        volume_data: 2D array (list of rows) for the slice, shape [ny, nx].
        slice_axis: Axis sliced along ("x", "y", or "z").
        slice_index: Index of the slice in the volume.
        nx: Number of samples in x direction.
        ny: Number of samples in y direction.
        attribute_name: Seismic/attribute name label.
        colormap: WebGL colormap name (e.g. "seismic", "jet", "viridis").
        vmin: Minimum display amplitude (auto-computed if None).
        vmax: Maximum display amplitude (auto-computed if None).
        session_id: Optional session ID for VAULT999 receipt.

    Returns:
        Dict with flat_data (normalised 0–1), shape, colormap, vmin/vmax,
        and VAULT999 receipt ready for WebGL rendering.
    """
    arr = np.array(volume_data, dtype=np.float64)
    rows, cols = arr.shape if arr.ndim == 2 else (1, len(arr))
    ny_actual = ny or rows
    nx_actual = nx or cols

    valid = arr[~np.isnan(arr)]
    data_vmin = float(np.min(valid)) if len(valid) > 0 else -1.0
    data_vmax = float(np.max(valid)) if len(valid) > 0 else 1.0

    display_vmin = vmin if vmin is not None else data_vmin
    display_vmax = vmax if vmax is not None else data_vmax

    # Normalise to [0, 1] for WebGL texture upload
    range_val = max(display_vmax - display_vmin, 1e-12)
    normalised = ((arr - display_vmin) / range_val).clip(0.0, 1.0)
    flat_data = normalised.flatten().tolist()

    vault_receipt = _make_vault("render_volume_slice", session_id)

    return {
        "render_type": "volume_slice",
        "attribute_name": attribute_name,
        "slice_axis": slice_axis,
        "slice_index": slice_index,
        "nx": nx_actual,
        "ny": ny_actual,
        "colormap": colormap,
        "vmin": round(display_vmin, 6),
        "vmax": round(display_vmax, 6),
        "flat_data": flat_data,
        "claim_tag": ClaimTag.CLAIM.value,
        "vault_receipt": vault_receipt,
        "audit_trace": (
            f"volume_slice|axis={slice_axis}|idx={slice_index}|"
            f"shape=[{ny_actual},{nx_actual}]|attr={attribute_name}"
        ),
    }
