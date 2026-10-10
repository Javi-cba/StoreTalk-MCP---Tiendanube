"""Order state changes: close, reopen, cancel and internal note."""

from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from src.mcp_server import context
from src.mcp_server.context import StoreContext
from src.mcp_server.tools.orders.lookup import find_order
from src.mcp_server.tools.orders.schemas import OrderDetail, order_detail
from src.services.tiendanube.models import TNOrder
from src.services.tiendanube.resources.orders import CancelReason


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Close order", openWorldHint=True))
    async def close_order(
        number: Annotated[int | None, Field(gt=0)] = None,
        order_id: Annotated[int | None, Field(gt=0)] = None,
    ) -> OrderDetail:
        """Archive (close) an order that is already finished."""
        ctx = await context.get_store_context()
        order = await find_order(ctx, order_id, number)
        if order.status == "closed":
            raise ToolError(f"La orden #{order.number} ya está cerrada.")
        updated = await context.run_tiendanube(ctx, lambda: ctx.client.orders.close(order.id))
        await audit_order(ctx, "close_order", order, updated)
        return order_detail(updated, ctx)

    @mcp.tool(annotations=ToolAnnotations(title="Reopen order", openWorldHint=True))
    async def reopen_order(
        number: Annotated[int | None, Field(gt=0)] = None,
        order_id: Annotated[int | None, Field(gt=0)] = None,
    ) -> OrderDetail:
        """Reopen a closed order."""
        ctx = await context.get_store_context()
        order = await find_order(ctx, order_id, number)
        if order.status == "open":
            raise ToolError(f"La orden #{order.number} ya está abierta.")
        if order.status == "cancelled":
            raise ToolError(f"La orden #{order.number} está cancelada y no se puede reabrir.")
        updated = await context.run_tiendanube(ctx, lambda: ctx.client.orders.reopen(order.id))
        await audit_order(ctx, "reopen_order", order, updated)
        return order_detail(updated, ctx)

    @mcp.tool(
        annotations=ToolAnnotations(title="Cancel order", destructiveHint=True, openWorldHint=True)
    )
    async def cancel_order(
        reason: Annotated[
            CancelReason, Field(description="customer, inventory (no stock), fraud or other.")
        ],
        number: Annotated[int | None, Field(gt=0)] = None,
        order_id: Annotated[int | None, Field(gt=0)] = None,
        notify_customer: Annotated[
            bool, Field(description="Email the buyer about the cancellation.")
        ] = True,
        restock: Annotated[bool, Field(description="Return the items to stock.")] = True,
    ) -> OrderDetail:
        """Cancel an order. Cannot be undone: confirm the order number with the user first.
        It does not refund the payment automatically.
        """
        ctx = await context.get_store_context()
        order = await find_order(ctx, order_id, number)
        if order.status == "cancelled":
            raise ToolError(f"La orden #{order.number} ya está cancelada.")
        updated = await context.run_tiendanube(
            ctx,
            lambda: ctx.client.orders.cancel(
                order.id, reason=reason, notify_customer=notify_customer, restock=restock
            ),
        )
        await audit_order(ctx, "cancel_order", order, updated)
        return order_detail(updated, ctx)

    @mcp.tool(annotations=ToolAnnotations(title="Set order note", openWorldHint=True))
    async def update_order_note(
        note: Annotated[
            str, Field(max_length=2000, description="Internal note (buyer can't see it).")
        ],
        number: Annotated[int | None, Field(gt=0)] = None,
        order_id: Annotated[int | None, Field(gt=0)] = None,
    ) -> OrderDetail:
        """Set the internal seller note of an order (replaces the previous note)."""
        ctx = await context.get_store_context()
        order = await find_order(ctx, order_id, number)
        updated = await context.run_tiendanube(
            ctx, lambda: ctx.client.orders.update_note(order.id, note)
        )
        await audit_order(ctx, "update_order_note", order, updated)
        return order_detail(updated, ctx)


async def audit_order(ctx: StoreContext, tool_name: str, before: TNOrder, after: TNOrder) -> None:
    # Only status fields: orders carry buyer personal data that the audit log must not keep.
    keys = ("status", "payment_status", "shipping_status", "owner_note", "cancel_reason")
    await context.record_audit(
        ctx,
        tool_name=tool_name,
        entity_type="order",
        entity_id=before.id,
        before={k: getattr(before, k) for k in keys},
        after={k: getattr(after, k) for k in keys},
    )
