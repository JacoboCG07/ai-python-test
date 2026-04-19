"""
Punto de entrada ASGI: composición de dependencias y registro de rutas.

Flujo: POST /v1/requests → POST .../process (pipeline asíncrono) → GET ...
El proveedor simulado escucha en 127.0.0.1:3001 (misma red Docker con
network_mode: service:provider).
"""
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from api.routes.requests import router as requests_router
from config import get_settings
from infrastructure.memory_store import MemoryRequestStore
from infrastructure.provider_client import ProviderClient
from services.llm_response_parser import LlmResponseParser
from services.notification_pipeline import NotificationPipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Cliente HTTP compartido y casos de uso cableados en `app.state`.
    """
    settings = get_settings()
    store = MemoryRequestStore()
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=50)
    client = httpx.AsyncClient(
        base_url=settings.provider_base,
        timeout=httpx.Timeout(settings.http_timeout_seconds),
        limits=limits,
    )
    provider = ProviderClient(client=client, settings=settings)
    parser = LlmResponseParser()
    pipeline = NotificationPipeline(
        store=store,
        provider=provider,
        parser=parser,
        settings=settings,
    )
    app.state.store = store
    app.state.pipeline = pipeline
    app.state.settings = settings
    yield
    await client.aclose()


app = FastAPI(
    title="Notification Service (Technical Test)",
    lifespan=lifespan,
)
app.include_router(requests_router)
