"""
Implementación en memoria del almacén de solicitudes (concurrencia con asyncio.Lock).
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, Optional, Tuple

from core.ports import PipelineStart
from models.schemas import StatusLiteral


class MemoryRequestStore:
    """
    Responsable únicamente del ciclo de vida del registro y del estado.
    """

    def __init__(self
    ) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def create_intake(self, user_input: str
    ) -> str:
        req_id = str(uuid.uuid4())
        async with self._lock:
            self._data[req_id] = {"user_input": user_input, "status": "queued"}
        return req_id

    async def try_begin_pipeline(self, req_id: str
    ) -> Tuple[PipelineStart, Optional[str]]:
        async with self._lock:
            rec = self._data.get(req_id)
            if rec is None:
                return ("missing", None)
            if rec["status"] in ("sent", "processing"):
                return ("noop", None)
            rec["status"] = "processing"
            return ("started", rec["user_input"])

    async def mark_failed_if_processing(self, req_id: str
    ) -> None:
        async with self._lock:
            rec = self._data.get(req_id)
            if rec is not None and rec["status"] == "processing":
                rec["status"] = "failed"

    async def mark_sent(self, req_id: str
    ) -> None:
        async with self._lock:
            rec = self._data.get(req_id)
            if rec is not None:
                rec["status"] = "sent"

    async def get_status(self, req_id: str
    ) -> Optional[StatusLiteral]:
        async with self._lock:
            rec = self._data.get(req_id)
            if rec is None:
                return None
            return rec["status"]
