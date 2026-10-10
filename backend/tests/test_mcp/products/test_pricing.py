import json

import respx

from tests.test_mcp.conftest import BASE_URL, Harness

CATEGORIES = [
    {"id": 5, "name": {"es": "Remeras"}, "parent": None, "subcategories": [7]},
    {"id": 7, "name": {"es": "Remeras manga larga"}, "parent": 5, "subcategories": []},
]
P1 = {
    "id": 1,
    "name": {"es": "Remera"},
    "variants": [{"id": 10, "price": "1000.00", "promotional_price": "900.00"}],
}
P2 = {"id": 2, "name": {"es": "Manga larga"}, "variants": [{"id": 20, "price": "1999.00"}]}


def _mock_catalog() -> None:
    respx.get(f"{BASE_URL}/categories").respond(200, json=CATEGORIES)
    respx.get(f"{BASE_URL}/products", params={"category_id": "5"}).respond(200, json=[P1])
    respx.get(f"{BASE_URL}/products", params={"category_id": "7"}).respond(200, json=[P2, P1])


@respx.mock
async def test_dry_run_only_previews(harness: Harness) -> None:
    _mock_catalog()
    patch = respx.patch(url__regex=rf"{BASE_URL}/products/\d+/variants").respond(200, json=[])

    data = await harness.call(
        "adjust_prices_by_category", {"category": "remeras", "percentage": 10}
    )

    assert not patch.called
    assert data["dry_run"] is True
    assert data["products_matched"] == 2  # P1 deduplicated across subcategories
    assert data["categories_included"] == ["Remeras", "Remeras > Remeras manga larga"]
    first = data["preview"][0]
    assert (first["old_price"], first["new_price"]) == ("1000.00", "1100.00")
    assert first["new_promotional_price"] == "990.00"


@respx.mock
async def test_apply_patches_each_product_once(harness: Harness) -> None:
    _mock_catalog()
    p1 = respx.patch(f"{BASE_URL}/products/1/variants").respond(200, json=[])
    p2 = respx.patch(f"{BASE_URL}/products/2/variants").respond(200, json=[])

    data = await harness.call(
        "adjust_prices_by_category",
        {"category": 5, "percentage": 10, "dry_run": False, "rounding": "tens"},
    )

    assert json.loads(p1.calls.last.request.content) == [
        {"id": 10, "price": "1100.00", "promotional_price": "990.00"}
    ]
    assert json.loads(p2.calls.last.request.content) == [{"id": 20, "price": "2200.00"}]
    assert data["completed"] is True
    assert data["variants_updated"] == 2
    assert harness.audits[0]["tool_name"] == "adjust_prices_by_category"


@respx.mock
async def test_partial_failures_are_reported(harness: Harness) -> None:
    _mock_catalog()
    respx.patch(f"{BASE_URL}/products/1/variants").respond(422, json={"price": ["invalid"]})
    respx.patch(f"{BASE_URL}/products/2/variants").respond(200, json=[])

    data = await harness.call(
        "adjust_prices_by_category", {"category": 5, "percentage": 10, "dry_run": False}
    )

    assert data["products_updated"] == 1
    assert "price: invalid" in data["failed"][0]
