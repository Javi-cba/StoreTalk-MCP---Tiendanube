import httpx
import pytest
import respx

from src.services.tiendanube.client import TiendanubeClient
from src.services.tiendanube.errors import TiendanubeAuthError, TiendanubeMissingScopeError
from src.services.tiendanube.scopes import Scope, is_granted, parse_granted

BASE = "https://api.tiendanube.com/2025-03/1"


def test_write_scope_implies_read() -> None:
    granted = parse_granted("write_products")
    assert is_granted(Scope.READ_PRODUCTS, granted)
    assert not is_granted(Scope.READ_ORDERS, granted)
    assert not is_granted(Scope.WRITE_COUPONS, parse_granted("read_coupons"))


@respx.mock
async def test_missing_scope_is_detected_before_calling_tiendanube() -> None:
    route = respx.post(f"{BASE}/coupons").respond(201, json={})
    async with httpx.AsyncClient() as http:
        client = TiendanubeClient(http, 1, "t", ["read_products", "read_coupons"])
        with pytest.raises(TiendanubeMissingScopeError) as exc:
            await client.coupons.create({"code": "X", "type": "shipping"})
    assert exc.value.scope == Scope.WRITE_COUPONS
    assert "`write_coupons`" in exc.value.message
    assert "StoreTalk" in exc.value.message
    assert not route.called


@respx.mock
@pytest.mark.parametrize("status", [401, 403])
async def test_unauthorized_on_scoped_call_names_the_scope(status: int) -> None:
    respx.get(f"{BASE}/orders/5").respond(status, json={"code": status, "message": "Forbidden"})
    async with httpx.AsyncClient() as http:
        with pytest.raises(TiendanubeMissingScopeError, match="`read_orders`"):
            await TiendanubeClient(http, 1, "t").orders.get(5)


@respx.mock
async def test_invalid_token_is_an_auth_error_not_a_scope_error() -> None:
    respx.get(f"{BASE}/products/5").respond(
        401, json={"code": 401, "message": "Unauthorized", "description": "Invalid access token"}
    )
    async with httpx.AsyncClient() as http:
        with pytest.raises(TiendanubeAuthError):
            await TiendanubeClient(http, 1, "t").products.get(5)
