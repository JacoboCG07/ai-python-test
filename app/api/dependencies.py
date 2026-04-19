"""
Dependencias resueltas desde `app.state` (inyectadas en los endpoints).
"""
from typing import Annotated

from fastapi import Depends, Request

from infrastructure.memory_store import MemoryRequestStore
from services.notification_pipeline import NotificationPipeline


def get_store(request: Request
) -> MemoryRequestStore:
    return request.app.state.store


def get_pipeline(request: Request
) -> NotificationPipeline:
    return request.app.state.pipeline


StoreDep = Annotated[MemoryRequestStore, Depends(get_store)]
PipelineDep = Annotated[NotificationPipeline, Depends(get_pipeline)]
