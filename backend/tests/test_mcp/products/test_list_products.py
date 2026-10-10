from typing import Any

import respx

from tests.test_mcp.conftest import BASE_URL, Harness

PRODUCTS_URL = f"{BASE_URL}/products"

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


async def _call(harness: Harness, args: dict[str, Any]) -> dict[str, Any]:
    return await harness.call("list_products", args)


@respx.mock
async def test_list_products_without_filters(harness: Harness) -> None:
    route = respx.get(PRODUCTS_URL).respond(
        200,
        json=[PRODUCT],
        headers={"x-total-count": "41", "Link": f'<{PRODUCTS_URL}?page=2>; rel="next"'},
    )

    data = await _call(harness, {})

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
async def test_list_products_with_filters_are_sent_to_tiendanube(harness: Harness) -> None:
    route = respx.get(PRODUCTS_URL).respond(200, json=[], headers={"x-total-count": "0"})

    data = await _call(
        harness, {"q": "remera", "published": False, "max_stock": 0, "sort_by": "best-selling"}
    )

    params = route.calls.last.request.url.params
    assert params["q"] == "remera"
    assert params["published"] == "false"
    assert params["max_stock"] == "0"
    assert params["sort_by"] == "best-selling"
    assert data["products"] == []
    assert data["has_more"] is False


@respx.mock
async def test_list_products_unlimited_stock_is_null(harness: Harness) -> None:
    product = {**PRODUCT, "variants": [{"id": 10, "price": "5.00", "stock": None}]}
    respx.get(PRODUCTS_URL).respond(200, json=[product])

    data = await _call(harness, {})

    assert data["products"][0]["stock_total"] is None


@respx.mock
async def test_list_products_empty_page_404_returns_empty(harness: Harness) -> None:
    respx.get(PRODUCTS_URL).respond(404, json={"code": 404, "message": "Not Found"})

    data = await _call(harness, {"page": 9})

    assert data["products"] == []
    assert data["has_more"] is False
