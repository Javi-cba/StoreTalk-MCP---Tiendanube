import json

import httpx
import respx

from tests.test_mcp.conftest import BASE_URL, Harness

PRODUCT = {
    "id": 1,
    "name": {"es": "Remera"},
    "attributes": [{"es": "Color"}, {"es": "Talle"}],
    "variants": [
        {
            "id": 10,
            "sku": "REM-ROJO-S",
            "price": "1000.00",
            "stock": 4,
            "image_id": 70,
            "values": [{"es": "Rojo"}, {"es": "S"}],
        },
        {
            "id": 11,
            "sku": "REM-AZUL-S",
            "price": "1200.00",
            "stock": 2,
            "image_id": 71,
            "values": [{"es": "Azul"}, {"es": "S"}],
        },
    ],
    "images": [{"id": 70, "src": "https://x/1.jpg"}, {"id": 71, "src": "https://x/2.jpg"}],
}


@respx.mock
async def test_add_size_creates_one_per_color_inheriting_from_siblings(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/products/1").respond(200, json=PRODUCT)
    created_ids = iter([20, 21])

    def create(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        return httpx.Response(201, json={"id": next(created_ids), **body})

    route = respx.post(f"{BASE_URL}/products/1/variants").mock(side_effect=create)

    data = await harness.call(
        "add_product_variants", {"product_id": 1, "variants": [{"values": {"talla": "l"}}]}
    )

    bodies = [json.loads(c.request.content) for c in route.calls]
    assert [b["values"] for b in bodies] == [
        [{"es": "Rojo"}, {"es": "L"}],
        [{"es": "Azul"}, {"es": "L"}],
    ]
    assert [b["price"] for b in bodies] == ["1000.00", "1200.00"]
    assert [b["sku"] for b in bodies] == ["REM-ROJO-L", "REM-AZUL-L"]
    assert [b["image_id"] for b in bodies] == [70, 71]
    assert [b["stock"] for b in bodies] == [0, 0]
    assert len(data["created"]) == 2
    assert data["created"][0]["values"] == {"Color": "Rojo", "Talle": "L"}
    assert any("Talle" in a for a in data["assumptions"])
    assert harness.audits[0]["tool_name"] == "add_product_variants"


@respx.mock
async def test_existing_combination_is_not_duplicated(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/products/1").respond(200, json=PRODUCT)
    route = respx.post(f"{BASE_URL}/products/1/variants").respond(201, json={"id": 9})

    data = await harness.call(
        "add_product_variants",
        {"product_id": 1, "variants": [{"values": {"Color": "rojo", "Talle": "s"}}]},
    )

    assert not route.called
    assert data["skipped_existing"] == [{"Color": "Rojo", "Talle": "S"}]


@respx.mock
async def test_new_attribute_asks_for_current_variant_value(harness: Harness) -> None:
    simple = {**PRODUCT, "attributes": [], "variants": [{"id": 10, "price": "5", "values": []}]}
    respx.get(f"{BASE_URL}/products/1").respond(200, json=simple)

    message = await harness.call_error(
        "add_product_variants", {"product_id": 1, "variants": [{"values": {"Talle": "L"}}]}
    )

    assert "existing_variant_values" in message


@respx.mock
async def test_new_attribute_converts_current_variant(harness: Harness) -> None:
    simple = {
        **PRODUCT,
        "attributes": [],
        "variants": [{"id": 10, "price": "5.00", "stock": None, "values": []}],
    }
    respx.get(f"{BASE_URL}/products/1").respond(200, json=simple)
    put = respx.put(f"{BASE_URL}/products/1").respond(200, json=simple)
    patch = respx.patch(f"{BASE_URL}/products/1/variants").respond(200, json=[])
    post = respx.post(f"{BASE_URL}/products/1/variants").respond(
        201, json={"id": 11, "price": "5.00", "values": [{"es": "L"}]}
    )

    await harness.call(
        "add_product_variants",
        {
            "product_id": 1,
            "variants": [{"values": {"talle": "l"}}],
            "existing_variant_values": {"Talle": "m"},
        },
    )

    assert json.loads(put.calls.last.request.content) == {"attributes": [{"es": "Talle"}]}
    assert json.loads(patch.calls.last.request.content) == [{"id": 10, "values": [{"es": "M"}]}]
    body = json.loads(post.calls.last.request.content)
    assert body["values"] == [{"es": "L"}]
    assert body["stock"] == ""  # sibling has unlimited stock


@respx.mock
async def test_update_variant_found_by_values(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/products/1").respond(200, json=PRODUCT)
    blue_s = {"id": 11, "price": "1200.00", "values": [{"es": "Azul"}, {"es": "S"}]}
    route = respx.put(f"{BASE_URL}/products/1/variants/11").respond(
        200, json={**blue_s, "stock": 9}
    )

    data = await harness.call(
        "update_variant", {"product_id": 1, "values": {"color": "azul"}, "stock": 9}
    )

    assert json.loads(route.calls.last.request.content) == {"stock": 9}
    assert data["stock"] == 9


@respx.mock
async def test_delete_variant_by_values(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/products/1").respond(200, json=PRODUCT)
    route = respx.delete(f"{BASE_URL}/products/1/variants/10").respond(200, json={})

    data = await harness.call(
        "delete_variant", {"product_id": 1, "values": {"Color": "Rojo", "Talle": "S"}}
    )

    assert route.called
    assert data["values"] == {"Color": "Rojo", "Talle": "S"}
