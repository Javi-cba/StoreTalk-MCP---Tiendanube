import json

import respx

from tests.test_mcp.conftest import BASE_URL, Harness

ORDER = {
    "id": 500,
    "number": 1234,
    "status": "open",
    "payment_status": "paid",
    "shipping_status": "unpacked",
    "total": "5000.00",
    "currency": "ARS",
    "products": [{"product_id": 1, "name": "Remera", "quantity": 2, "price": "2500.00"}],
}


@respx.mock
async def test_list_orders_sends_filters(harness: Harness) -> None:
    route = respx.get(f"{BASE_URL}/orders").respond(200, json=[ORDER])

    data = await harness.call("list_orders", {"payment_status": "paid"})

    assert route.calls.last.request.url.params["payment_status"] == "paid"
    assert data["orders"][0]["number"] == 1234
    assert data["orders"][0]["items_count"] == 2


@respx.mock
async def test_cancel_order_by_number(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/orders").respond(200, json=[ORDER])
    route = respx.post(f"{BASE_URL}/orders/500/cancel").respond(
        200, json={**ORDER, "status": "cancelled", "cancel_reason": "inventory"}
    )

    data = await harness.call(
        "cancel_order", {"number": 1234, "reason": "inventory", "notify_customer": False}
    )

    assert json.loads(route.calls.last.request.content) == {
        "reason": "inventory",
        "email": False,
        "restock": True,
    }
    assert data["status"] == "cancelled"
    assert harness.audits[0]["before"]["status"] == "open"


@respx.mock
async def test_close_already_closed_order_is_explained(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/orders/500").respond(200, json={**ORDER, "status": "closed"})
    message = await harness.call_error("close_order", {"order_id": 500})
    assert "ya está cerrada" in message


@respx.mock
async def test_get_order_without_customer_scope_explains_it(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/orders/500").respond(200, json=ORDER)
    data = await harness.call("get_order", {"order_id": 500})
    assert any("`read_customers`" in n for n in data["notes"])
