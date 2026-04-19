"""
Cliente HTTP hacia el proveedor simulado (extract + notify) con reintentos.
"""
from __future__ import annotations

from typing import Any, Dict, List

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from config import Settings


class ProviderClient:
    """
    Adaptador concreto sobre httpx.AsyncClient inyectado (testable / sustituible).
    """

    def __init__(self, client: httpx.AsyncClient, settings: Settings
    ) -> None:
        self._client = client
        self._settings = settings

    @retry(
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
        stop=stop_after_attempt(18),
        wait=wait_exponential_jitter(initial=0.15, max=10),
        reraise=True,
    )
    async def _post_extract_raw(self, payload: Dict[str, Any]
    ) -> httpx.Response:
        response = await self._client.post(
            self._settings.extract_path,
            json=payload,
            headers={
                "X-API-Key": self._settings.api_key,
                "Content-Type": "application/json",
            },
        )
        if response.status_code in (429, 500):
            response.raise_for_status()
        if response.status_code != 200:
            response.raise_for_status()
        return response

    @retry(
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
        stop=stop_after_attempt(18),
        wait=wait_exponential_jitter(initial=0.15, max=10),
        reraise=True,
    )
    async def _post_notify_raw(self, payload: Dict[str, Any]
    ) -> httpx.Response:
        response = await self._client.post(
            self._settings.notify_path,
            json=payload,
            headers={
                "X-API-Key": self._settings.api_key,
                "Content-Type": "application/json",
            },
        )
        if response.status_code in (429, 500):
            response.raise_for_status()
        if response.status_code != 200:
            response.raise_for_status()
        return response

    async def extract(self, messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        resp = await self._post_extract_raw({"messages": messages})
        return resp.json()

    async def notify(self, payload: Dict[str, str]
    ) -> None:
        await self._post_notify_raw(payload)
