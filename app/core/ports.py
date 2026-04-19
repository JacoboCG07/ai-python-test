"""
Contratos (Protocol) para invertir dependencias: la capa de dominio/servicios
no acopla a implementaciones concretas de almacenamiento o HTTP.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Protocol, Tuple

from models.schemas import StatusLiteral

PipelineStart = Literal["missing", "noop", "started"]


class RequestStorePort(Protocol):
    """
    Persistencia en memoria de solicitudes y sus estados.
    """

    async def create_intake(self, user_input: str
    ) -> str:
        ...

    async def try_begin_pipeline(self, req_id: str
    ) -> Tuple[PipelineStart, Optional[str]]:
        ...

    async def mark_failed_if_processing(self, req_id: str
    ) -> None:
        ...

    async def mark_sent(self, req_id: str
    ) -> None:
        ...

    async def get_status(self, req_id: str
    ) -> Optional[StatusLiteral]:
        ...


class ProviderPort(Protocol):
    """
    Acceso al proveedor externo (extracción IA y notificación).
    """

    async def extract(self, messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        ...

    async def notify(self, payload: Dict[str, str]
    ) -> None:
        ...
