"""
LAS Ingestor — Real-Time LAS 2.0/3.0 Ingestion Pipeline.
DITEMPA BUKAN DIBERI

Uses lasio to parse LAS files. Extracts:
  - Header metadata: UWI, KB elevation, datum, CRS
  - Curve manifest: mnemonics, units, depth range
  - QC flags: spike detection, PhysicsGuard range checks

Returns LASManifest with curve_manifest, depth range, QC flags, asset_id.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import lasio  # type: ignore[import-untyped]
import numpy as np

from geox.core.ac_risk import ClaimTag
from geox.core.physics_guard import PhysicsGuard

_guard = PhysicsGuard()

# PhysicsGuard bounds for QC (extended for raw log curves)
_CURVE_BOUNDS: dict[str, tuple[float, float]] = {
    "GR": (0.0, 300.0),       # API units
    "RT": (0.1, 10000.0),     # ohm.m
    "RHOB": (1.5, 3.2),       # g/cc
    "NPHI": (-0.05, 0.60),    # v/v
    "SW": (0.0, 1.0),         # v/v
    "POR": (0.02, 0.45),      # v/v (PhysicsGuard)
    "VSH": (0.0, 1.0),        # v/v
    "CAL": (3.0, 30.0),       # inches
    "SP": (-200.0, 50.0),     # mV
}

# Spike detection threshold: if value > mean ± N * std it's a spike
_SPIKE_STD_FACTOR = 5.0


@dataclass
class CurveQC:
    """QC result for a single curve."""
    mnemonic: str
    unit: str
    n_samples: int
    null_pct: float
    range_min: float
    range_max: float
    out_of_bounds_pct: float
    spike_count: int
    qc_pass: bool
    qc_flags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mnemonic": self.mnemonic,
            "unit": self.unit,
            "n_samples": self.n_samples,
            "null_pct": round(self.null_pct, 4),
            "range_min": round(self.range_min, 4),
            "range_max": round(self.range_max, 4),
            "out_of_bounds_pct": round(self.out_of_bounds_pct, 4),
            "spike_count": self.spike_count,
            "qc_pass": self.qc_pass,
            "qc_flags": self.qc_flags,
        }


@dataclass
class LASManifest:
    """Full manifest of an ingested LAS file."""
    asset_id: str
    well_name: str
    uwi: str
    kb_elevation_m: float | None
    datum: str
    crs: str
    depth_range_m: tuple[float, float]
    depth_unit: str
    n_curves: int
    n_depth_samples: int
    curves: list[CurveQC]
    overall_qc_pass: bool
    claim_tag: str
    vault_receipt: dict[str, Any]
    audit_trace: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "well_name": self.well_name,
            "uwi": self.uwi,
            "kb_elevation_m": self.kb_elevation_m,
            "datum": self.datum,
            "crs": self.crs,
            "depth_range_m": list(self.depth_range_m),
            "depth_unit": self.depth_unit,
            "n_curves": self.n_curves,
            "n_depth_samples": self.n_depth_samples,
            "curves": [c.to_dict() for c in self.curves],
            "overall_qc_pass": self.overall_qc_pass,
            "claim_tag": self.claim_tag,
            "vault_receipt": self.vault_receipt,
            "audit_trace": self.audit_trace,
        }


def _null_pct(arr: np.ndarray) -> float:
    if arr is None or len(arr) == 0:
        return 1.0
    return float(np.sum(np.isnan(arr)) / len(arr))


def _canonicalise(arr: np.ndarray) -> np.ndarray:
    """Replace LAS null sentinels with np.nan."""
    arr = np.array(arr, dtype=np.float64)
    null_sentinels = {-999.25, -999.0, -9999.0, -9999.25}
    for nv in null_sentinels:
        arr[arr == nv] = np.nan
    return arr


def _spike_count(arr: np.ndarray, n_sigma: float = _SPIKE_STD_FACTOR) -> int:
    valid = arr[~np.isnan(arr)]
    if len(valid) < 10:
        return 0
    mean = np.mean(valid)
    std = np.std(valid)
    if std == 0:
        return 0
    return int(np.sum(np.abs(valid - mean) > n_sigma * std))


def _out_of_bounds_pct(arr: np.ndarray, lo: float, hi: float) -> float:
    valid = arr[~np.isnan(arr)]
    if len(valid) == 0:
        return 0.0
    return float(np.sum((valid < lo) | (valid > hi)) / len(valid))


def _qc_curve(mnemonic: str, unit: str, arr: np.ndarray) -> CurveQC:
    """Run QC checks on a single curve array."""
    arr_c = _canonicalise(arr)
    valid = arr_c[~np.isnan(arr_c)]
    flags: list[str] = []

    null_p = _null_pct(arr_c)
    if null_p > 0.5:
        flags.append(f"HIGH_NULL_PCT:{null_p:.1%}")

    if len(valid) == 0:
        return CurveQC(
            mnemonic=mnemonic, unit=unit, n_samples=len(arr_c),
            null_pct=null_p, range_min=0.0, range_max=0.0,
            out_of_bounds_pct=0.0, spike_count=0,
            qc_pass=False, qc_flags=["ALL_NULL"],
        )

    r_min = float(np.min(valid))
    r_max = float(np.max(valid))
    spikes = _spike_count(arr_c)
    if spikes > 0:
        flags.append(f"SPIKES:{spikes}")

    oob_pct = 0.0
    mnem_upper = mnemonic.upper()
    if mnem_upper in _CURVE_BOUNDS:
        lo, hi = _CURVE_BOUNDS[mnem_upper]
        oob_pct = _out_of_bounds_pct(arr_c, lo, hi)
        if oob_pct > 0.05:
            flags.append(f"OUT_OF_BOUNDS:{oob_pct:.1%}")

    qc_pass = len(flags) == 0
    return CurveQC(
        mnemonic=mnemonic, unit=unit, n_samples=len(arr_c),
        null_pct=null_p, range_min=r_min, range_max=r_max,
        out_of_bounds_pct=oob_pct, spike_count=spikes,
        qc_pass=qc_pass, qc_flags=flags,
    )


class LASIngestor:
    """LAS 2.0 / 3.0 ingestion and QC pipeline.

    Parses LAS files using lasio. Extracts header metadata and runs
    per-curve QC against PhysicsGuard bounds.
    """

    def ingest(
        self,
        filepath: str,
        asset_id: str | None = None,
        session_id: str | None = None,
    ) -> LASManifest:
        """Parse and QC a LAS file.

        Args:
            filepath: Path to .las file.
            asset_id: Optional asset/field identifier. Defaults to well name.
            session_id: Optional session ID for VAULT999 receipt.

        Returns:
            LASManifest with full curve QC and provenance.

        Raises:
            FileNotFoundError: If filepath does not exist.
            ValueError: If no depth curve found.
        """
        import os
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"LAS file not found: {filepath}")

        las = lasio.read(filepath)

        # ---- Header extraction ----
        well_name = str(las.well.get("WELL", {}).value if hasattr(las.well.get("WELL", {}), "value") else "")
        if not well_name:
            well_name = str(getattr(las.well.get("WELL", ""), "value", "") or "UNKNOWN")
        uwi = self._header_value(las, ["UWI", "API", "LEASE"])
        kb_elevation = self._header_float(las, ["KB", "KELEV", "DKBE"])
        datum = self._header_value(las, ["DATUM", "EPSG"])
        crs = self._header_value(las, ["CRS", "COORDSYS", "PROJ"])
        depth_unit = self._header_value(las, ["DUN", "STOP"])

        # ---- Depth curve ----
        depth_arr: np.ndarray | None = None
        for key in ("DEPT", "DEPTH", "MD", "MEAS"):
            if key in las.curves:
                depth_arr = _canonicalise(las[key].data)
                break

        if depth_arr is None or len(depth_arr) == 0:
            raise ValueError(f"No depth curve found in {filepath}. Tried: DEPT, DEPTH, MD, MEAS.")

        depth_range = (float(np.nanmin(depth_arr)), float(np.nanmax(depth_arr)))

        # ---- Curve QC ----
        qc_results: list[CurveQC] = []
        for curve in las.curves:
            mnem = curve.mnemonic.upper()
            if mnem in ("DEPT", "DEPTH", "MD", "MEAS"):
                continue  # skip depth itself
            arr = _canonicalise(curve.data)
            unit = getattr(curve, "unit", "") or ""
            qc_results.append(_qc_curve(mnem, unit, arr))

        overall_pass = all(c.qc_pass for c in qc_results) if qc_results else True
        resolved_asset_id = asset_id or well_name or "UNKNOWN_ASSET"

        # Epistemic tag
        claim_tag = ClaimTag.CLAIM.value if overall_pass else ClaimTag.PLAUSIBLE.value

        # VAULT999 receipt
        ts = datetime.now(timezone.utc).isoformat()
        receipt_payload = f"las_ingest|{resolved_asset_id}|curves={len(qc_results)}|{ts}"
        vault_receipt = {
            "epoch": int(time.time()),
            "session_id": session_id or "N/A",
            "hash": hashlib.sha256(receipt_payload.encode()).hexdigest()[:16],
            "overall_qc_pass": overall_pass,
            "timestamp": ts,
        }

        audit_trace = (
            f"asset={resolved_asset_id} well={well_name} uwi={uwi} "
            f"| depth_range={depth_range} n_curves={len(qc_results)} "
            f"| qc_pass={overall_pass}"
        )

        return LASManifest(
            asset_id=resolved_asset_id,
            well_name=well_name,
            uwi=uwi,
            kb_elevation_m=kb_elevation,
            datum=datum,
            crs=crs,
            depth_range_m=depth_range,
            depth_unit=depth_unit or "m",
            n_curves=len(qc_results),
            n_depth_samples=len(depth_arr),
            curves=qc_results,
            overall_qc_pass=overall_pass,
            claim_tag=claim_tag,
            vault_receipt=vault_receipt,
            audit_trace=audit_trace,
        )

    @staticmethod
    def _header_value(las: lasio.LasFile, keys: list[str]) -> str:
        for key in keys:
            entry = las.well.get(key)
            if entry is not None:
                val = getattr(entry, "value", None)
                if val is not None and str(val).strip():
                    return str(val).strip()
        return "UNKNOWN"

    @staticmethod
    def _header_float(las: lasio.LasFile, keys: list[str]) -> float | None:
        for key in keys:
            entry = las.well.get(key)
            if entry is not None:
                val = getattr(entry, "value", None)
                try:
                    return float(val)
                except (TypeError, ValueError):
                    continue
        return None
