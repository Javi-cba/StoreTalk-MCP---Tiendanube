"""Read-only order tools: list and get."""

from datetime import datetime
from typing import Annotated

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from src.mcp_server import context
from src.mcp_server.tools.orders.lookup import find_order
from src.mcp_server.tools.orders.schemas import (
    LIST_FIELDS,
    OrderDetail,
    OrderListResult,
    OrderStatus,
    PaymentStatus,
    ShippingStatus,
    order_detail,
    order_summary,
)
from src.services.tiendanube.models import TNOrder


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(title="List orders", readOnlyHint=True, openWorldHint=True)
    )
    async def list_orders(
        status: Annotated[
            OrderStatus | None, Field(description="Use any to include closed and cancelled orders.")
        ] = None,
        payment_status: PaymentStatus | None = None,
        shipping_status: ShippingStatus | None = None,
        q: Annotated[str | None, Field(description="Order number, or buyer name / email.")] = None,
        created_at_min: Annotated[datetime | None, Field(description="ISO 8601.")] = None,
        created_at_max: Annotated[datetime | None, Field(description="ISO 8601.")] = None,
        page: Annotated[int, Field(ge=1)] = 1,
        per_page: Annotated[int, Field(ge=1, le=50)] = 20,
    ) -> OrderListResult:
        """List orders, newest first, with filters (status, payment, shipping, dates, search).
        e.g. paid orders pending shipment: payment_status='paid', shipping_status='unpacked'.
        """
        ctx = await context.get_store_context()
        params = {
            "status": status,
            "payment_status": payment_status,
            "shipping_status": shipping_status,
            "q": q,
            "created_at_min": created_at_min.isoformat() if created_at_min else None,
            "created_at_max": created_at_max.isoformat() if created_at_max else None,
            "page": page,
            "per_page": per_page,
            "fields": LIST_FIELDS,
        }
        result = await context.run_tiendanube(ctx, lambda: ctx.client.orders.list(params))
        return OrderListResult(
            orders=[order_summary(TNOrder.model_validate(i)) for i in result.items],
            page=page,
            total=result.total,
            has_more=result.has_more,
        )

    @mcp.tool(annotations=ToolAnnotations(title="Get order", readOnlyHint=True, openWorldHint=True))
    async def get_order(
        number: Annotated[int | None, Field(gt=0, description="Order number (#1234).")] = None,
        order_id: Annotated[int | None, Field(gt=0)] = None,
    ) -> OrderDetail:
        """Full detail of one order: items, totals, coupons, payment, shipping and notes."""
        ctx = await context.get_store_context()
        order = await find_order(ctx, order_id, number)
        if order_id is None:  # the list payload is partial: fetch the full order
            order = await context.run_tiendanube(ctx, lambda: ctx.client.orders.get(order.id))
        return order_detail(order, ctx)
