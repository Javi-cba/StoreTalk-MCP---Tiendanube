import httpx
import pytest
import respx

from src.services.tiendanube.client import TiendanubeClient
from src.services.tiendanube.errors import TiendanubeAuthError, TiendanubeValidationError

STORE_URL = "https://api.tiendanube.com/2025-03/1/store"


@respx.mock
async def test_retries_429_then_succeeds() -> None:
    route = respx.get(STORE_URL).mock(
        side_effect=[
            httpx.Response(429, headers={"x-rate-limit-reset": "10"}),
            httpx.Response(200, json={"id": 1, "name": {"es": "Mi tienda"}}),
        ]
    )
    async with httpx.AsyncClient() as http:
        store = await TiendanubeClient(http, 1, "t").get_store()
    assert store.id == 1
    assert route.call_count == 2


@respx.mock
async def test_401_raises_auth_error() -> None:
    respx.get(STORE_URL).respond(401)
    async with httpx.AsyncClient() as http:
        with pytest.raises(TiendanubeAuthError):
            await TiendanubeClient(http, 1, "t").get_store()


@respx.mock
async def test_422_is_readable() -> None:
    respx.get(STORE_URL).respond(422, json={"price": ["must be positive"]})
    async with httpx.AsyncClient() as http:
        with pytest.raises(TiendanubeValidationError, match="price: must be positive"):
            await TiendanubeClient(http, 1, "t").get_store()
