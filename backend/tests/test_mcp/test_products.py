import uuid
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
import respx
from fastmcp import Client, FastMCP

from src.mcp_server import context as context_module
from src.mcp_server.context import StoreContext
from src.mcp_server.server import create_mcp
from src.mcp_server.tools import products as products_module
from src.services.tiendanube.client import TiendanubeClient

STORE_ID = 999
PRODUCTS_URL = f"https://api.tiendanube.com/2025-03/{STORE_ID}/products"

PRODUCT = {
    "id": 1,
    "name": {"es": "Remera azul", "pt": "Camiseta azul"},
    "handle": {"es": "remera-azul"},
    "published": True,
    "brand": None,
    "variants": [
        {"id": 10, "sku": "REM-AZ-S", "price": "1000.00", "promotional_price": None, "stock": 3},
        {
            "id": 11,
            "sku": "REM-AZ-M",
            "price": "1200.00",
            "promotional_price": "999.00",
            "stock": 2,
        },
    ],
    "categories": [{"id": 5, "name": {"es": "Remeras"}}],
    "images": [{"id": 7, "src": "https://cdn.example.com/1.jpg"}],
    "updated_at": "2026-10-01T10:00:00+0000",
}


@pytest.fixture
async def mcp(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[FastMCP]:
    async with httpx.AsyncClient() as http:
        store_ctx = StoreContext(
            connection_id=uuid.uuid4(),
            store_id=STORE_ID,
            language="es",
            client=TiendanubeClient(http, STORE_ID, "token"),
        )

        async def fake_context() -> StoreContext:
            return store_ctx

        monkeypatch.setattr(products_module, "get_store_context", fake_context)
        monkeypatch.setattr(context_module, "get_store_context", fake_context)
        yield create_mcp(auth=None)


async def _call(mcp: FastMCP, args: dict[str, Any]) -> dict[str, Any]:
    async with Client(mcp) as client:
        result = await client.call_tool("list_products", args)
    assert result.structured_content is not None
    return result.structured_content


@respx.mock
async def test_list_products_without_filters(mcp: FastMCP) -> None:
    route = respx.get(PRODUCTS_URL).respond(
        200,
        json=[PRODUCT],
        headers={"x-total-count": "41", "Link": f'<{PRODUCTS_URL}?page=2>; rel="next"'},
    )

    data = await _call(mcp, {})

    params = route.calls.last.request.url.params
    assert params["page"] == "1"
    assert params["per_page"] == "20"
    assert "q" not in params
    assert route.calls.last.request.headers["Authorization"] == "Bearer token"
    assert data["total"] == 41
    assert data["has_more"] is True
    product = data["products"][0]
    assert product["name"] == "Remera azul"
    assert product["stock_total"] == 5
    assert product["on_promotion"] is True
    assert product["categories"] == ["Remeras"]
    assert product["skus"] == ["REM-AZ-S", "REM-AZ-M"]


@respx.mock
async def test_list_products_with_filters_are_sent_to_tiendanube(mcp: FastMCP) -> None:
    route = respx.get(PRODUCTS_URL).respond(200, json=[], headers={"x-total-count": "0"})

    data = await _call(
        mcp, {"q": "remera", "published": False, "max_stock": 0, "sort_by": "best-selling"}
    )

    params = route.calls.last.request.url.params
    assert params["q"] == "remera"
    assert params["published"] == "false"
    assert params["max_stock"] == "0"
    assert params["sort_by"] == "best-selling"
    assert data["products"] == []
    assert data["has_more"] is False


@respx.mock
async def test_list_products_unlimited_stock_is_null(mcp: FastMCP) -> None:
    product = {**PRODUCT, "variants": [{"id": 10, "price": "5.00", "stock": None}]}
    respx.get(PRODUCTS_URL).respond(200, json=[product])

    data = await _call(mcp, {})

    assert data["products"][0]["stock_total"] is None


@respx.mock
async def test_list_products_empty_page_404_returns_empty(mcp: FastMCP) -> None:
    respx.get(PRODUCTS_URL).respond(404, json={"code": 404, "message": "Not Found"})

    data = await _call(mcp, {"page": 9})

    assert data["products"] == []
    assert data["has_more"] is False
