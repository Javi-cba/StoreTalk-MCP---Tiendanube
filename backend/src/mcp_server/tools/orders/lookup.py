"""Find an order by id or by the number the buyer sees (#1234)."""

from fastmcp.exceptions import ToolError

from src.mcp_server import context
from src.mcp_server.context import StoreContext
from src.services.tiendanube.models import TNOrder


async def find_order(ctx: StoreContext, order_id: int | None, number: int | None) -> TNOrder:
    """Users talk about the order number (#1234); the API needs the id."""
    if order_id is not None:
        return await context.run_tiendanube(ctx, lambda: ctx.client.orders.get(order_id))
    if number is None:
        raise ToolError("Indicá el número de la orden (ej. 1234) o su id.")
    page = await context.run_tiendanube(
        ctx, lambda: ctx.client.orders.list({"q": number, "status": "any", "per_page": 10})
    )
    for item in page.items:
        order = TNOrder.model_validate(item)
        if order.number == number:
            return order
    raise ToolError(f"No existe la orden #{number}.")
