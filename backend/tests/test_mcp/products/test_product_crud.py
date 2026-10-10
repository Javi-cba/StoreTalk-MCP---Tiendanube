import base64
import json

import respx

from tests.test_mcp.conftest import BASE_URL, Harness

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
CATEGORIES = [
    {"id": 5, "name": {"es": "Remeras"}, "parent": None, "subcategories": []},
    {"id": 6, "name": {"es": "Pantalones"}, "parent": None, "subcategories": []},
]
CREATED = {
    "id": 1,
    "name": {"es": "Remera lisa"},
    "attributes": [{"es": "Talle"}],
    "variants": [
        {"id": 10, "price": "1000.00", "stock": 5, "values": [{"es": "S"}]},
        {"id": 11, "price": "1000.00", "stock": 2, "values": [{"es": "M"}]},
    ],
    "categories": [{"id": 5, "name": {"es": "Remeras"}}],
    "images": [],
}


@respx.mock
async def test_create_product_with_variants_categories_and_images(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/categories").respond(200, json=CATEGORIES)
    create = respx.post(f"{BASE_URL}/products").respond(201, json=CREATED)
    upload = respx.post(f"{BASE_URL}/products/1/images").respond(
        201, json={"id": 70, "src": "https://cdn/x.png", "position": 2}
    )
    respx.get(f"{BASE_URL}/products/1").respond(200, json=CREATED)

    data = await harness.call(
        "create_product",
        {
            "name": "Remera lisa",
            "price": 1000,
            "stock": 5,
            "categories": ["remera"],
            "tags": ["algodon", "verano"],
            "variants": [{"values": {"Talle": "s"}}, {"values": {"Talle": "m"}, "stock": 2}],
            "images": [
                {"url": "https://example.com/front.jpg"},
                {"base64": base64.b64encode(PNG).decode(), "filename": "back.jpeg"},
            ],
        },
    )

    body = json.loads(create.calls.last.request.content)
    assert body["name"] == {"es": "Remera lisa"}
    assert body["attributes"] == [{"es": "Talle"}]
    assert [v["values"] for v in body["variants"]] == [[{"es": "S"}], [{"es": "M"}]]
    assert [v["stock"] for v in body["variants"]] == [5, 2]
    assert body["variants"][0]["price"] == "1000"
    assert body["categories"] == [5]
    assert body["tags"] == "algodon,verano"
    assert body["images"] == [{"src": "https://example.com/front.jpg"}]
    uploaded = json.loads(upload.calls.last.request.content)
    assert uploaded["filename"] == "back.png"  # real format, not the claimed extension
    assert data["id"] == 1
    assert harness.audits[0]["tool_name"] == "create_product"


async def test_create_product_rejects_unsupported_image(harness: Harness) -> None:
    bmp = base64.b64encode(b"BM" + b"\x00" * 30).decode()
    message = await harness.call_error(
        "create_product", {"name": "X", "price": 1, "images": [{"base64": bmp}]}
    )
    assert "JPG, PNG, GIF o WEBP" in message


@respx.mock
async def test_unknown_category_suggests_close_names(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/categories").respond(200, json=CATEGORIES)
    message = await harness.call_error(
        "create_product", {"name": "X", "price": 1, "categories": ["Pantalon corto"]}
    )
    assert "No existe la categoría" in message


@respx.mock
async def test_update_price_applies_to_all_variants(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/products/1").respond(200, json=CREATED)
    patch = respx.patch(f"{BASE_URL}/products/1/variants").respond(200, json=[])
    put = respx.put(f"{BASE_URL}/products/1").respond(200, json=CREATED)

    await harness.call("update_product", {"product_id": 1, "price": 1500})

    assert json.loads(patch.calls.last.request.content) == [
        {"id": 10, "price": "1500"},
        {"id": 11, "price": "1500"},
    ]
    assert not put.called


@respx.mock
async def test_get_product_by_sku(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/products/sku/ABC").respond(200, json=CREATED)
    data = await harness.call("get_product", {"sku": "ABC"})
    assert data["attributes"] == ["Talle"]
    assert data["variants"][1]["values"] == {"Talle": "M"}


@respx.mock
async def test_delete_product(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/products/1").respond(200, json=CREATED)
    route = respx.delete(f"{BASE_URL}/products/1").respond(200, json={})
    data = await harness.call("delete_product", {"product_id": 1})
    assert route.called
    assert data == {"id": 1, "name": "Remera lisa", "deleted": True}
    assert harness.audits[0]["after"] is None


@respx.mock
async def test_validation_error_is_readable(harness: Harness) -> None:
    respx.post(f"{BASE_URL}/products").respond(
        422,
        json={
            "code": 422,
            "message": "Unprocessable Entity",
            "description": "Store has reached maximum limit of 100000 allowed products",
        },
    )
    message = await harness.call_error("create_product", {"name": "X", "price": 1})
    assert "maximum limit" in message
