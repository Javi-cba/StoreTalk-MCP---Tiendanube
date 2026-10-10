import respx

from tests.test_mcp.conftest import BASE_URL, Harness


@respx.mock
async def test_tool_error_tells_which_scope_to_add(harness: Harness) -> None:
    harness.set_scopes("read_products")
    route = respx.get(f"{BASE_URL}/coupons/3").respond(200, json={})

    message = await harness.call_error("delete_coupon", {"coupon_id": 3})

    assert "`read_coupons`" in message
    assert "admin de StoreTalk" in message
    assert not route.called


@respx.mock
async def test_scope_rejected_by_tiendanube_is_reported(harness: Harness) -> None:
    harness.set_scopes("")  # legacy connection: scopes unknown, no pre-flight
    respx.get(f"{BASE_URL}/orders").respond(401, json={"code": 401, "message": "Unauthorized"})

    message = await harness.call_error("list_orders")

    assert "`read_orders`" in message
