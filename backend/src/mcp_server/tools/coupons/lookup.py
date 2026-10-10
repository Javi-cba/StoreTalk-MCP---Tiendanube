"""Find a coupon by id or by code."""

from fastmcp.exceptions import ToolError

from src.mcp_server import context
from src.mcp_server.context import StoreContext
from src.mcp_server.tools.coupons.rules import normalize_code
from src.mcp_server.tools.coupons.schemas import COUPON_FIELDS
from src.services.tiendanube.models import TNCoupon


async def find_coupon(ctx: StoreContext, coupon_id: int | None, code: str | None) -> TNCoupon:
    if coupon_id is not None:
        return await context.run_tiendanube(ctx, lambda: ctx.client.coupons.get(coupon_id))
    if not code:
        raise ToolError("Indicá el id o el código del cupón.")
    wanted = normalize_code(code)
    page = await context.run_tiendanube(
        ctx,
        lambda: ctx.client.coupons.list({"q": wanted, "per_page": 50, "fields": COUPON_FIELDS}),
    )
    for item in page.items:
        coupon = TNCoupon.model_validate(item)
        if coupon.code.upper() == wanted:
            return coupon
    raise ToolError(f"No existe un cupón con el código '{wanted}'.")
