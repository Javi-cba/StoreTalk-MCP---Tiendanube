"""Single entry point for every Tiendanube call (rate limit, retries, error mapping).

Docs: https://tiendanube.github.io/api-documentation/intro
"""

import asyncio
import logging
from typing import Any

import httpx

from src.config import get_settings
from src.services.tiendanube import rate_limit
from src.services.tiendanube.errors import (
    TiendanubeAuthError,
    TiendanubeError,
    TiendanubeNotFoundError,
    TiendanubePaymentRequiredError,
    TiendanubeRateLimitError,
    TiendanubeUnavailableError,
    TiendanubeValidationError,
)
from src.services.tiendanube.models import TNPage, TNStore

logger = logging.getLogger(__name__)

TIMEOUT = httpx.Timeout(20.0, connect=5.0)
MAX_ATTEMPTS = 3
IDEMPOTENT_METHODS = frozenset({"GET", "PUT", "DELETE"})
MAX_PER_PAGE = 200

_http: httpx.AsyncClient | None = None


def create_http_client() -> httpx.AsyncClient:
    global _http
    _http = httpx.AsyncClient(timeout=TIMEOUT)
    return _http


async def close_http_client() -> None:
    global _http
    if _http is not None:
        await _http.aclose()
        _http = None


def get_http_client() -> httpx.AsyncClient:
    if _http is None:
        raise RuntimeError("HTTP client not initialized (app lifespan not running)")
    return _http


class TiendanubeClient:
    def __init__(self, http: httpx.AsyncClient, store_id: int, access_token: str) -> None:
        settings = get_settings()
        self._http = http
        self.store_id = store_id
        self._base_url = (
            f"{settings.tiendanube_api_base}/{settings.tiendanube_api_version}/{store_id}"
        )
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": settings.tiendanube_user_agent,
            "Content-Type": "application/json",
        }

    async def _request(
        self, method: str, path: str, *, params: dict[str, Any] | None = None
    ) -> httpx.Response:
        url = f"{self._base_url}{path}"
        last_error: TiendanubeError | None = None
        for attempt in range(MAX_ATTEMPTS):
            async with rate_limit.store_semaphore(self.store_id):
                try:
                    response = await self._http.request(
                        method, url, params=params, headers=self._headers
                    )
                except httpx.TransportError as exc:
                    last_error = TiendanubeUnavailableError(
                        "Tiendanube no respondió a tiempo. Probá de nuevo en unos segundos."
                    )
                    logger.warning(
                        "tiendanube transport error",
                        extra={"store_id": self.store_id, "error": type(exc).__name__},
                    )
                    if method not in IDEMPOTENT_METHODS:
                        raise last_error from exc
                    await asyncio.sleep(2**attempt * 0.5)
                    continue

            if response.status_code == 429:
                last_error = TiendanubeRateLimitError(
                    "Tiendanube está limitando las consultas de esta tienda. "
                    "Esperá unos segundos y volvé a intentar."
                )
                await asyncio.sleep(rate_limit.retry_after_429(response, attempt))
                continue
            if response.status_code >= 500 and method in IDEMPOTENT_METHODS:
                last_error = TiendanubeUnavailableError(
                    "Tiendanube tiene un problema temporal. Probá de nuevo en unos minutos."
                )
                await asyncio.sleep(2**attempt * 0.5)
                continue

            self._raise_for_status(response, path)
            delay = rate_limit.throttle_delay(response)
            if delay:
                await asyncio.sleep(delay)
            return response

        assert last_error is not None
        raise last_error

    @staticmethod
    def _raise_for_status(response: httpx.Response, path: str) -> None:
        status = response.status_code
        if status < 400:
            return
        if status == 401:
            raise TiendanubeAuthError(
                "La tienda se desconectó de StoreTalk. Reconectala desde el dashboard."
            )
        if status == 402:
            raise TiendanubePaymentRequiredError(
                "Tiendanube suspendió el acceso de la app a esta tienda (pago pendiente)."
            )
        if status == 404:
            raise TiendanubeNotFoundError(f"No se encontró el recurso solicitado ({path}).")
        if status == 422:
            raise TiendanubeValidationError(
                f"Tiendanube rechazó los datos enviados: {_validation_detail(response)}"
            )
        if status >= 500:
            raise TiendanubeUnavailableError(
                "Tiendanube tiene un problema temporal. Probá de nuevo en unos minutos."
            )
        raise TiendanubeError(f"Tiendanube devolvió un error inesperado (HTTP {status}).")

    async def get_store(self) -> TNStore:
        """GET /store — https://tiendanube.github.io/api-documentation/resources/store"""
        response = await self._request("GET", "/store")
        return TNStore.model_validate(response.json())

    async def list_products(self, params: dict[str, Any]) -> TNPage:
        """GET /products — https://tiendanube.github.io/api-documentation/resources/product

        Filters (q, category_id, published, min_stock, ...), `page`/`per_page` (max 200)
        and `fields` are passed straight to Tiendanube; nothing is filtered in Python.
        Pagination: `x-total-count` and `Link` (rel="next") headers.
        """
        clean = {k: _to_query_value(v) for k, v in params.items() if v is not None}
        try:
            response = await self._request("GET", "/products", params=clean)
        except TiendanubeNotFoundError:
            # Tiendanube answers 404 when a page has no results.
            return TNPage(items=[], total=0, has_more=False)
        total_header = response.headers.get("x-total-count")
        return TNPage(
            items=response.json(),
            total=int(total_header) if total_header and total_header.isdigit() else None,
            has_more="next" in response.links,
        )


def _to_query_value(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list | tuple):
        return ",".join(str(v) for v in value)
    return value


def _validation_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return "datos inválidos"
    if isinstance(body, dict):
        parts = [
            f"{field}: {', '.join(map(str, msgs)) if isinstance(msgs, list) else msgs}"
            for field, msgs in body.items()
            if field not in {"code", "message"}
        ]
        if parts:
            return "; ".join(parts)
        if "description" in body:
            return str(body["description"])
    return "datos inválidos"
