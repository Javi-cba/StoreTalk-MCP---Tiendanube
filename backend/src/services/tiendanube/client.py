"""Single entry point for every Tiendanube call (rate limit, retries, scopes, error mapping).

Docs: https://tiendanube.github.io/api-documentation/intro
Endpoints live in one resource class per entity (`resources/`), exposed as attributes:
`client.products`, `client.variants`, `client.images`, `client.categories`,
`client.coupons`, `client.orders`.
"""

import asyncio
import logging
from collections.abc import Iterable
from typing import Any

import httpx

from src.config import get_settings
from src.services.tiendanube import rate_limit
from src.services.tiendanube.errors import (
    TiendanubeAuthError,
    TiendanubeError,
    TiendanubeMissingScopeError,
    TiendanubeNotFoundError,
    TiendanubePaymentRequiredError,
    TiendanubeRateLimitError,
    TiendanubeUnavailableError,
    TiendanubeValidationError,
)
from src.services.tiendanube.models import TNPage, TNStore
from src.services.tiendanube.resources.categories import CategoriesResource
from src.services.tiendanube.resources.coupons import CouponsResource
from src.services.tiendanube.resources.images import ImagesResource
from src.services.tiendanube.resources.orders import OrdersResource
from src.services.tiendanube.resources.products import ProductsResource
from src.services.tiendanube.resources.variants import VariantsResource
from src.services.tiendanube.scopes import Scope, is_granted, parse_granted

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
    def __init__(
        self,
        http: httpx.AsyncClient,
        store_id: int,
        access_token: str,
        granted_scopes: Iterable[str] = (),
    ) -> None:
        settings = get_settings()
        self._http = http
        self.store_id = store_id
        # Empty = unknown (legacy connections): skip the pre-flight check, rely on the API.
        self.granted_scopes = parse_granted(granted_scopes)
        self._base_url = (
            f"{settings.tiendanube_api_base}/{settings.tiendanube_api_version}/{store_id}"
        )
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": settings.tiendanube_user_agent,
            "Content-Type": "application/json",
        }
        self.products = ProductsResource(self)
        self.variants = VariantsResource(self)
        self.images = ImagesResource(self)
        self.categories = CategoriesResource(self)
        self.coupons = CouponsResource(self)
        self.orders = OrdersResource(self)

    async def request(
        self,
        method: str,
        path: str,
        *,
        scope: Scope | None,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> httpx.Response:
        """`scope` is the OAuth scope the endpoint needs (None = no specific scope)."""
        if scope and self.granted_scopes and not is_granted(scope, self.granted_scopes):
            raise TiendanubeMissingScopeError(scope)
        url = f"{self._base_url}{path}"
        clean_params = (
            {k: _to_query_value(v) for k, v in params.items() if v is not None} if params else None
        )
        last_error: TiendanubeError | None = None
        for attempt in range(MAX_ATTEMPTS):
            async with rate_limit.store_semaphore(self.store_id):
                try:
                    response = await self._http.request(
                        method, url, params=clean_params, json=json, headers=self._headers
                    )
                except httpx.TransportError as exc:
                    last_error = TiendanubeUnavailableError(
                        "Tiendanube no respondió a tiempo. Probá de nuevo en unos segundos."
                    )
                    logger.warning(
                        "tiendanube transport error",
                        extra={"store_id": self.store_id, "error": type(exc).__name__},
                    )
                    # Never retry a POST/PATCH blindly: it may have been applied.
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

            self._raise_for_status(response, scope)
            delay = rate_limit.throttle_delay(response)
            if delay:
                await asyncio.sleep(delay)
            return response

        assert last_error is not None
        raise last_error

    async def get_json(
        self, path: str, *, scope: Scope | None, params: dict[str, Any] | None = None
    ) -> Any:
        response = await self.request("GET", path, scope=scope, params=params)
        return response.json()

    async def get_page(self, path: str, *, scope: Scope, params: dict[str, Any]) -> TNPage:
        """Paginated GET. `x-total-count` + `Link` (rel="next") headers.

        Tiendanube answers 404 when a page has no results: mapped to an empty page.
        """
        try:
            response = await self.request("GET", path, scope=scope, params=params)
        except TiendanubeNotFoundError:
            return TNPage(items=[], total=0, has_more=False)
        total_header = response.headers.get("x-total-count")
        return TNPage(
            items=response.json(),
            total=int(total_header) if total_header and total_header.isdigit() else None,
            has_more="next" in response.links,
        )

    async def send(self, method: str, path: str, *, scope: Scope, json: Any = None) -> Any:
        """Write request. Returns the JSON body (Tiendanube answers `{}` on DELETE)."""
        response = await self.request(method, path, scope=scope, json=json)
        return response.json() if response.content else {}

    def _raise_for_status(self, response: httpx.Response, scope: Scope | None) -> None:
        status = response.status_code
        if status < 400:
            return
        if status in (401, 403):
            # A missing scope must never revoke the connection: only an invalid token does.
            # Tiendanube's body for a bad token: {"description": "Invalid access token"}.
            # Calls that need no scope can only fail because of the token.
            invalid_token = "access token" in _error_detail(response, default="").lower()
            if status == 401 and (invalid_token or scope is None):
                raise TiendanubeAuthError(
                    "La tienda se desconectó de StoreTalk. Reconectala desde el dashboard."
                )
            if scope is None:
                raise TiendanubeError("Tiendanube denegó el acceso a este recurso.")
            raise TiendanubeMissingScopeError(scope)
        if status == 402:
            raise TiendanubePaymentRequiredError(
                "Tiendanube suspendió el acceso de la app a esta tienda (pago pendiente)."
            )
        if status == 404:
            raise TiendanubeNotFoundError(
                _error_detail(response, default="No se encontró el recurso solicitado.")
            )
        if status in (400, 422):
            raise TiendanubeValidationError(
                f"Tiendanube rechazó los datos enviados: {_error_detail(response)}"
            )
        if status >= 500:
            raise TiendanubeUnavailableError(
                "Tiendanube tiene un problema temporal. Probá de nuevo en unos minutos."
            )
        raise TiendanubeError(f"Tiendanube devolvió un error inesperado (HTTP {status}).")

    async def get_store(self) -> TNStore:
        """GET /store — https://tiendanube.github.io/api-documentation/resources/store"""
        return TNStore.model_validate(await self.get_json("/store", scope=None))


def _to_query_value(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list | tuple):
        return ",".join(str(v) for v in value)
    return value


def _error_detail(response: httpx.Response, default: str = "datos inválidos") -> str:
    """Tiendanube errors come in three shapes (docs: intro + each resource page):
    `{"name": ["can't be blank"]}`, `{"code", "message", "description"}`, or both mixed.
    """
    try:
        body = response.json()
    except ValueError:
        return default
    if not isinstance(body, dict):
        return default
    parts = [
        f"{field}: {', '.join(map(str, msgs)) if isinstance(msgs, list) else msgs}"
        for field, msgs in body.items()
        if field not in {"code", "message", "description", "error"}
    ]
    if parts:
        return "; ".join(parts)
    for key in ("description", "error", "message"):
        if body.get(key):
            return str(body[key])
    return default
