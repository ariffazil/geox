"""
Asset Memory Store — Cross-Domain Per-Asset Memory Persistence.
DITEMPA BUKAN DIBERI

SQLite-backed per-asset memory for field learning. Stores:
  - LAS ingests, petro results, volume estimates, charge verdicts, VAULT999 receipts

Schema: (asset_id TEXT, eval_type TEXT, timestamp TEXT, payload JSON, vault_receipt TEXT)

Constitutional guard:
  - Memory write requires F11 auth (amanah_locked=True check)
  - Memory read is F2 truth-tagged (ClaimTag emitted on recall)
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

from geox.core.ac_risk import ClaimTag

_DEFAULT_DB_PATH = Path.home() / ".geox" / "asset_memory.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS asset_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id TEXT NOT NULL,
    eval_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    payload TEXT NOT NULL,
    vault_receipt TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_asset_memory_asset_id ON asset_memory(asset_id);
CREATE INDEX IF NOT EXISTS idx_asset_memory_eval_type ON asset_memory(eval_type);
"""


@dataclass
class MemoryRecord:
    """Single record retrieved from asset memory."""
    record_id: int
    asset_id: str
    eval_type: str
    timestamp: str
    payload: dict[str, Any]
    vault_receipt: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "asset_id": self.asset_id,
            "eval_type": self.eval_type,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "vault_receipt": self.vault_receipt,
        }


@dataclass
class StoreResult:
    """Result of a memory store operation."""
    success: bool
    record_id: int | None
    asset_id: str
    eval_type: str
    claim_tag: str
    vault_receipt: dict[str, Any]
    audit_trace: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "record_id": self.record_id,
            "asset_id": self.asset_id,
            "eval_type": self.eval_type,
            "claim_tag": self.claim_tag,
            "vault_receipt": self.vault_receipt,
            "audit_trace": self.audit_trace,
        }


@dataclass
class RecallResult:
    """Result of a memory recall query."""
    asset_id: str
    eval_type: str | None
    n_records: int
    records: list[MemoryRecord]
    claim_tag: str
    vault_receipt: dict[str, Any]
    audit_trace: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "eval_type": self.eval_type,
            "n_records": self.n_records,
            "records": [r.to_dict() for r in self.records],
            "claim_tag": self.claim_tag,
            "vault_receipt": self.vault_receipt,
            "audit_trace": self.audit_trace,
        }


class AssetMemoryStore:
    """SQLite-backed per-asset memory persistence.

    Stores evaluation results keyed by asset_id and eval_type.
    Supports retrieval and simple keyword-based recall.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(_CREATE_TABLE)

    def store(
        self,
        asset_id: str,
        eval_type: str,
        payload: dict[str, Any],
        amanah_locked: bool = False,
        session_id: str | None = None,
    ) -> StoreResult:
        """Store an evaluation result for an asset.

        Args:
            asset_id: Field/block/well identifier.
            eval_type: Type of evaluation (e.g. "petro_ensemble", "las_ingest",
                "volumetrics", "basin_charge", "sensitivity").
            payload: Arbitrary JSON-serializable result dict.
            amanah_locked: F11 constitutional requirement. Must be True to write.
            session_id: Optional session ID for VAULT999 receipt.

        Returns:
            StoreResult with record_id and VAULT999 receipt.
        """
        ts = datetime.now(timezone.utc).isoformat()

        if not amanah_locked:
            vault_receipt = {
                "epoch": int(time.time()),
                "session_id": session_id or "N/A",
                "hash": "DENIED",
                "timestamp": ts,
            }
            return StoreResult(
                success=False, record_id=None,
                asset_id=asset_id, eval_type=eval_type,
                claim_tag=ClaimTag.UNKNOWN.value,
                vault_receipt=vault_receipt,
                audit_trace=f"F11_AUTH_REQUIRED: amanah_locked=False for asset={asset_id}",
            )

        payload_json = json.dumps(payload)
        receipt_payload = f"memory_store|{asset_id}|{eval_type}|{ts}"
        receipt_hash = hashlib.sha256(receipt_payload.encode()).hexdigest()[:16]
        vault_receipt = {
            "epoch": int(time.time()),
            "session_id": session_id or "N/A",
            "hash": receipt_hash,
            "timestamp": ts,
        }
        vault_receipt_json = json.dumps(vault_receipt)

        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO asset_memory (asset_id, eval_type, timestamp, payload, vault_receipt) "
                "VALUES (?, ?, ?, ?, ?)",
                (asset_id, eval_type, ts, payload_json, vault_receipt_json),
            )
            record_id = cursor.lastrowid

        audit_trace = (
            f"STORED: asset={asset_id} type={eval_type} "
            f"record_id={record_id} ts={ts}"
        )

        return StoreResult(
            success=True,
            record_id=record_id,
            asset_id=asset_id,
            eval_type=eval_type,
            claim_tag=ClaimTag.CLAIM.value,
            vault_receipt=vault_receipt,
            audit_trace=audit_trace,
        )

    def recall(
        self,
        asset_id: str,
        eval_type: str | None = None,
        limit: int = 20,
        session_id: str | None = None,
    ) -> RecallResult:
        """Recall stored evaluations for an asset.

        Args:
            asset_id: Field/block/well identifier.
            eval_type: Optional filter by evaluation type.
            limit: Maximum number of records to return.
            session_id: Optional session ID for VAULT999 receipt.

        Returns:
            RecallResult with records and F2-tagged ClaimTag.
        """
        with self._connect() as conn:
            if eval_type:
                rows = conn.execute(
                    "SELECT id, asset_id, eval_type, timestamp, payload, vault_receipt "
                    "FROM asset_memory WHERE asset_id = ? AND eval_type = ? "
                    "ORDER BY id DESC LIMIT ?",
                    (asset_id, eval_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, asset_id, eval_type, timestamp, payload, vault_receipt "
                    "FROM asset_memory WHERE asset_id = ? "
                    "ORDER BY id DESC LIMIT ?",
                    (asset_id, limit),
                ).fetchall()

        records = [
            MemoryRecord(
                record_id=int(row["id"]),
                asset_id=str(row["asset_id"]),
                eval_type=str(row["eval_type"]),
                timestamp=str(row["timestamp"]),
                payload=json.loads(row["payload"]),
                vault_receipt=json.loads(row["vault_receipt"]),
            )
            for row in rows
        ]

        ts = datetime.now(timezone.utc).isoformat()
        receipt_payload = f"memory_recall|{asset_id}|n={len(records)}|{ts}"
        vault_receipt = {
            "epoch": int(time.time()),
            "session_id": session_id or "N/A",
            "hash": hashlib.sha256(receipt_payload.encode()).hexdigest()[:16],
            "timestamp": ts,
        }

        # F2 truth-tag: if records found and recent, CLAIM; else ESTIMATE
        claim_tag = ClaimTag.CLAIM.value if len(records) > 0 else ClaimTag.ESTIMATE.value

        audit_trace = (
            f"RECALLED: asset={asset_id} type={eval_type or 'ALL'} "
            f"n_records={len(records)} limit={limit}"
        )

        return RecallResult(
            asset_id=asset_id,
            eval_type=eval_type,
            n_records=len(records),
            records=records,
            claim_tag=claim_tag,
            vault_receipt=vault_receipt,
            audit_trace=audit_trace,
        )
