import json

import respx

from tests.test_mcp.conftest import BASE_URL, Harness

CATEGORIES = [
    {"id": 1, "name": {"es": "Hombre"}, "parent": None},
    {"id": 2, "name": {"es": "Mujer"}, "parent": None},
    {"id": 3, "name": {"es": "Remeras"}, "parent": 1},
    {"id": 4, "name": {"es": "Remeras"}, "parent": 2},
]


@respx.mock
async def test_create_subcategory_by_parent_name(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/categories").respond(200, json=CATEGORIES)
    route = respx.post(f"{BASE_URL}/categories").respond(
        201, json={"id": 9, "name": {"es": "Buzos"}, "parent": 1}
    )

    data = await harness.call("create_category", {"name": "Buzos", "parent": "hombre"})

    assert json.loads(route.calls.last.request.content) == {"name": {"es": "Buzos"}, "parent": 1}
    assert data["path"] == "Hombre > Buzos"


@respx.mock
async def test_ambiguous_name_asks_for_path(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/categories").respond(200, json=CATEGORIES)
    message = await harness.call_error("delete_category", {"category": "Remeras"})
    assert "Hombre > Remeras" in message and "Mujer > Remeras" in message


@respx.mock
async def test_delete_by_path(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/categories").respond(200, json=CATEGORIES)
    route = respx.delete(f"{BASE_URL}/categories/4").respond(200, json={})
    data = await harness.call("delete_category", {"category": "Mujer > Remeras"})
    assert route.called
    assert data["name"] == "Mujer > Remeras"


@respx.mock
async def test_list_categories_with_paths(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/categories").respond(200, json=CATEGORIES)
    data = await harness.call("list_categories", {"q": "remera"})
    assert [c["path"] for c in data["categories"]] == ["Hombre > Remeras", "Mujer > Remeras"]
