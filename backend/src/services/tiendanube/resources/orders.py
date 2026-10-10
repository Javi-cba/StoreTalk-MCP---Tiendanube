"""Orders — https://tiendanube.github.io/api-documentation/resources/order

`customer` is only returned when the app also has `read_customers`.
PUT only changes `owner_note` and/or `status`; close/open/cancel have their own endpoints.
"""

from typing import Any, Literal

from src.services.tiendanube.models import TNOrder, TNPage
from src.services.tiendanube.resources._base import Resource
from src.services.tiendanube.scopes import Scope

CancelReason = Literal["customer", "inventory", "fraud", "other"]


class OrdersResource(Resource):
    async def list(self, params: dict[str, Any]) -> TNPage:
        """GET /orders. Filters: status, payment_status, shipping_status, q,
        created/updated_at_min/max, total_min/max, page, per_page, fields.
        """
        return await self._client.get_page("/orders", scope=Scope.READ_ORDERS, params=params)

    async def get(self, order_id: int) -> TNOrder:
        """GET /orders/{id}"""
        data = await self._client.get_json(f"/orders/{order_id}", scope=Scope.READ_ORDERS)
        return TNOrder.model_validate(data)

    async def update_note(self, order_id: int, owner_note: str) -> TNOrder:
        """PUT /orders/{id} with `owner_note` (internal note, not visible to the buyer)."""
        data = await self._client.send(
            "PUT", f"/orders/{order_id}", scope=Scope.WRITE_ORDERS, json={"owner_note": owner_note}
        )
        return TNOrder.model_validate(data)

    async def close(self, order_id: int) -> TNOrder:
        """POST /orders/{id}/close"""
        data = await self._client.send(
            "POST", f"/orders/{order_id}/close", scope=Scope.WRITE_ORDERS
        )
        return TNOrder.model_validate(data)

    async def reopen(self, order_id: int) -> TNOrder:
        """POST /orders/{id}/open"""
        data = await self._client.send("POST", f"/orders/{order_id}/open", scope=Scope.WRITE_ORDERS)
        return TNOrder.model_validate(data)

    async def cancel(
        self, order_id: int, *, reason: CancelReason, notify_customer: bool, restock: bool
    ) -> TNOrder:
        """POST /orders/{id}/cancel — body: reason, email (notify buyer), restock."""
        data = await self._client.send(
            "POST",
            f"/orders/{order_id}/cancel",
            scope=Scope.WRITE_ORDERS,
            json={"reason": reason, "email": notify_customer, "restock": restock},
        )
        return TNOrder.model_validate(data)
