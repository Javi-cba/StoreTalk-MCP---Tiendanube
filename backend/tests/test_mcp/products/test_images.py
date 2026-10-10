import json

import respx

from tests.test_mcp.conftest import BASE_URL, Harness

PRODUCT = {
    "id": 1,
    "name": {"es": "Remera"},
    "attributes": [{"es": "Color"}],
    "variants": [
        {"id": 10, "values": [{"es": "Rojo"}]},
        {"id": 11, "values": [{"es": "Azul"}]},
    ],
    "images": [],
}


@respx.mock
async def test_add_images_links_to_variants_and_reports_failures(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/products/1").respond(200, json=PRODUCT)
    respx.post(f"{BASE_URL}/products/1/images").respond(
        201, json={"id": 80, "src": "https://cdn/r.jpg", "position": 1}
    )
    patch = respx.patch(f"{BASE_URL}/products/1/variants").respond(200, json=[])

    data = await harness.call(
        "add_product_images",
        {
            "product_id": 1,
            "images": [{"url": "https://example.com/rojo.jpg"}, {"url": "ftp://bad"}],
            "for_variants": {"color": "rojo"},
        },
    )

    assert [i["id"] for i in data["uploaded"]] == [80]
    assert len(data["failed"]) == 1
    assert json.loads(patch.calls.last.request.content) == [{"id": 10, "image_id": 80}]
    assert data["linked_variant_ids"] == [10]


@respx.mock
async def test_delete_image(harness: Harness) -> None:
    route = respx.delete(f"{BASE_URL}/products/1/images/80").respond(200, json={})
    data = await harness.call("delete_product_image", {"product_id": 1, "image_id": 80})
    assert route.called
    assert data["deleted"] is True
