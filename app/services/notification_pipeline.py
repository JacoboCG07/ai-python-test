"""
Orquestación del flujo: IA → guardrails → notificación, actualizando el almacén.
"""
from __future__ import annotations

import asyncio
import logging

from config import Settings
from core.ports import ProviderPort, RequestStorePort

from .llm_response_parser import LlmResponseParser

logger = logging.getLogger(__name__)


class NotificationPipeline:
    """
    Caso de uso principal: coordina proveedor y persistencia sin conocer HTTP de FastAPI.
    """

    def __init__(
        self,
        store: RequestStorePort,
        provider: ProviderPort,
        parser: LlmResponseParser,
        settings: Settings,
        semaphore: asyncio.Semaphore | None = None,
    ) -> None:
        self._store = store
        self._provider = provider
        self._parser = parser
        self._settings = settings
        self._sem = semaphore or asyncio.Semaphore(settings.provider_max_parallel)

    async def run(self, req_id: str, user_input: str
    ) -> None:
        messages = [
            {"role": "system", "content": self._settings.extraction_system_prompt},
            {"role": "user", "content": user_input},
        ]
        try:
            async with self._sem:
                data = await self._provider.extract(messages)
        except Exception as exc:
            logger.warning("Extract failed for %s: %s", req_id, exc)
            await self._store.mark_failed_if_processing(req_id)
            return

        try:
            choices = data.get("choices") or []
            message = (choices[0].get("message") or {}) if choices else {}
            content = message.get("content")
            if not isinstance(content, str):
                raise ValueError("Missing assistant text content")
        except Exception as exc:
            logger.warning("Extract parse failed for %s: %s", req_id, exc)
            await self._store.mark_failed_if_processing(req_id)
            return

        payload = self._parser.parse(content)
        if payload is None:
            logger.warning("Could not normalize LLM output for %s", req_id)
            await self._store.mark_failed_if_processing(req_id)
            return

        try:
            async with self._sem:
                await self._provider.notify(payload)
        except Exception as exc:
            logger.warning("Delivery failed for %s: %s", req_id, exc)
            await self._store.mark_failed_if_processing(req_id)
            return

        await self._store.mark_sent(req_id)
