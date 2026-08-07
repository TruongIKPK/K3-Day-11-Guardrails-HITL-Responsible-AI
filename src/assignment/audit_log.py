"""
Assignment 11 — Audit Log starter (TODO).

Records every interaction for forensics. Never blocks by itself —
other layers catch attacks; this layer makes them reviewable.
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


class AuditLogPlugin:
    """Framework-agnostic audit logger (wire into ADK callbacks or your pipeline)."""

    def __init__(self):
        self.name = "audit_log"
        self.logs: list[dict] = []
        self._open: dict[str, dict] = {}

    def record_input(self, *, user_id: str, text: str, request_id: str | None = None) -> str:
        """Store input + start timestamp keyed by request_id/user_id."""
        req_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        self._open[req_id] = {
            "request_id": req_id,
            "user_id": user_id,
            "text": text,
            "start_time": time.time(),
            "timestamp": utc_now_iso(),
        }
        return req_id

    def record_output(
        self,
        *,
        user_id: str,
        text: str,
        blocked: bool = False,
        layer: str | None = None,
        request_id: str | None = None,
        reviewer_decision: str | None = None,
        action: str | None = None,
    ) -> dict:
        """Store output, layer decision, latency; append to self.logs."""
        req_id = request_id
        start_info = {}
        if req_id and req_id in self._open:
            start_info = self._open.pop(req_id)
        else:
            req_id = req_id or f"req_{uuid.uuid4().hex[:12]}"
            start_info = {
                "request_id": req_id,
                "user_id": user_id,
                "text": "",
                "start_time": time.time(),
                "timestamp": utc_now_iso(),
            }

        latency = time.time() - start_info["start_time"]

        entry = {
            "request_id": req_id,
            "user_id": user_id,
            "timestamp": start_info["timestamp"],
            "completed_at": utc_now_iso(),
            "input_text": start_info["text"],
            "output_text": text,
            "blocked": blocked,
            "layer": layer or "pipeline",
            "action": action or ("block" if blocked else "pass"),
            "reviewer_decision": reviewer_decision or ("N/A" if not blocked else "blocked_by_guardrail"),
            "latency_seconds": round(latency, 4),
        }
        self.logs.append(entry)
        return entry

    def find_by_request_id(self, request_id: str) -> dict | None:
        """Search and return the audit record matching request_id."""
        for log in self.logs:
            if log.get("request_id") == request_id:
                return log
        return None

    def export_json(self, filepath: str = "outputs/audit_log.json"):
        """Write logs to disk (JSON array)."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

