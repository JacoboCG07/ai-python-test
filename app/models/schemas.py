"""
Esquemas Pydantic expuestos por la API HTTP.
"""
from typing import Literal

from pydantic import BaseModel

StatusLiteral = Literal["queued", "processing", "sent", "failed"]


class IntakeCreate(BaseModel):
    """
    Cuerpo de POST /v1/requests.
    """

    user_input: str


class IntakeCreateResponse(BaseModel):
    """
    Respuesta 201 de creación.
    """

    id: str


class NotificationStatusResponse(BaseModel):
    """
    Respuesta de GET /v1/requests/{id}.
    """

    id: str
    status: StatusLiteral
