import json

import respx

from tests.test_mcp.conftest import BASE_URL, Harness

COUPON = {"id": 3, "code": "VERANO20", "type": "percentage", "value": "20.00", "valid": True}


@respx.mock
async def test_create_coupon_normalizes_code(harness: Harness) -> None:
    route = respx.post(f"{BASE_URL}/coupons").respond(201, json=COUPON)

    data = await harness.call(
        "create_coupon",
        {"code": "verano 20", "type": "percentage", "value": 20, "end_date": "2027-03-31"},
    )

    assert json.loads(route.calls.last.request.content) == {
        "code": "VERANO20",
        "type": "percentage",
        "value": "20",
        "end_date": "2027-03-31",
    }
    assert data["code"] == "VERANO20"


async def test_create_coupon_validations(harness: Harness) -> None:
    assert "entre 0 y 100" in await harness.call_error(
        "create_coupon", {"code": "X1", "type": "percentage", "value": 150}
    )
    assert "solo letras y números" in await harness.call_error(
        "create_coupon", {"code": "50%OFF", "type": "shipping"}
    )
    assert "no a ambos" in await harness.call_error(
        "create_coupon",
        {"code": "X1", "type": "absolute", "value": 5, "categories": [1], "product_ids": [2]},
    )


@respx.mock
async def test_delete_coupon_by_code(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/coupons").respond(200, json=[COUPON])
    route = respx.delete(f"{BASE_URL}/coupons/3").respond(200, json={})

    data = await harness.call("delete_coupon", {"code": "verano20"})

    assert route.called
    assert data == {"id": 3, "code": "VERANO20", "deleted": True}


@respx.mock
async def test_update_coupon_extends_end_date(harness: Harness) -> None:
    respx.get(f"{BASE_URL}/coupons/3").respond(200, json=COUPON)
    route = respx.put(f"{BASE_URL}/coupons/3").respond(200, json=COUPON)

    await harness.call("update_coupon", {"coupon_id": 3, "end_date": "2027-04-30"})

    assert json.loads(route.calls.last.request.content) == {
        "code": "VERANO20",
        "type": "percentage",
        "value": "20.00",
        "end_date": "2027-04-30",
    }
