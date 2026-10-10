"""Discount coupon tools: list, get, create, update, delete."""

from datetime import date
from decimal import Decimal
from typing import Annotated, Any

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from src.mcp_server import context
from src.mcp_server.tools.categories.resolver import CategoryRef, resolve_category_ids
from src.mcp_server.tools.coupons.lookup import find_coupon
from src.mcp_server.tools.coupons.rules import CouponStatus, CouponType, check_rules, normalize_code
from src.mcp_server.tools.coupons.schemas import (
    COUPON_FIELDS,
    CouponDeleted,
    CouponListResult,
    CouponSummary,
    summarize,
)
from src.services.tiendanube.models import TNCoupon


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(title="List coupons", readOnlyHint=True, openWorldHint=True)
    )
    async def list_coupons(
        q: Annotated[str | None, Field(description="Search by code.")] = None,
        valid: Annotated[bool | None, Field(description="Only usable / expired coupons.")] = None,
        status: Annotated[CouponStatus | None, Field()] = None,
        discount_type: Annotated[CouponType | None, Field()] = None,
        page: Annotated[int, Field(ge=1)] = 1,
        per_page: Annotated[int, Field(ge=1, le=50)] = 20,
    ) -> CouponListResult:
        """List the store's discount coupons (code, type, value, uses, dates, validity)."""
        ctx = await context.get_store_context()
        params = {
            "q": q,
            "valid": valid,
            "status": status,
            "discount_type": discount_type,
            "page": page,
            "per_page": per_page,
            "fields": COUPON_FIELDS,
        }
        result = await context.run_tiendanube(ctx, lambda: ctx.client.coupons.list(params))
        return CouponListResult(
            coupons=[summarize(TNCoupon.model_validate(i)) for i in result.items],
            page=page,
            total=result.total,
            has_more=result.has_more,
        )

    @mcp.tool(
        annotations=ToolAnnotations(title="Get coupon", readOnlyHint=True, openWorldHint=True)
    )
    async def get_coupon(
        coupon_id: Annotated[int | None, Field(gt=0)] = None,
        code: Annotated[str | None, Field(description="Coupon code, e.g. VERANO20.")] = None,
    ) -> CouponSummary:
        """Detail of one coupon by id or code (including how many times it was used)."""
        ctx = await context.get_store_context()
        return summarize(await find_coupon(ctx, coupon_id, code))

    @mcp.tool(annotations=ToolAnnotations(title="Create coupon", openWorldHint=True))
    async def create_coupon(
        code: Annotated[
            str, Field(min_length=1, description="Alphanumeric; normalized to uppercase.")
        ],
        type: Annotated[
            CouponType,
            Field(description="percentage (% off), absolute (fixed amount off), shipping (free)."),
        ],
        value: Annotated[
            Decimal | None,
            Field(gt=0, description="% or amount. Not needed for free shipping."),
        ] = None,
        start_date: Annotated[date | None, Field(description="YYYY-MM-DD.")] = None,
        end_date: Annotated[date | None, Field(description="YYYY-MM-DD.")] = None,
        max_uses: Annotated[int | None, Field(gt=0, description="Total uses allowed.")] = None,
        min_price: Annotated[
            Decimal | None, Field(gt=0, description="Minimum cart amount.")
        ] = None,
        categories: Annotated[
            list[CategoryRef] | None,
            Field(description="Only for these categories (names or ids)."),
        ] = None,
        product_ids: Annotated[
            list[int] | None, Field(description="Only for these products (not with categories).")
        ] = None,
        first_consumer_purchase: Annotated[
            bool | None, Field(description="Only the buyer's first purchase.")
        ] = None,
        combines_with_other_discounts: Annotated[
            bool | None, Field(description="Default true in Tiendanube.")
        ] = None,
        includes_shipping: Annotated[
            bool | None, Field(description="The discount also applies to shipping cost.")
        ] = None,
    ) -> CouponSummary:
        """Create a discount coupon. e.g. "20% off code VERANO until March" ->
        code='VERANO', type='percentage', value=20, end_date='2027-03-31'.
        """
        clean_code = normalize_code(code)
        check_rules(type, value, start_date, end_date, bool(categories), bool(product_ids))
        ctx = await context.get_store_context()
        payload: dict[str, Any] = {"code": clean_code, "type": type}
        optional: dict[str, Any] = {
            "value": str(value) if value is not None and type != "shipping" else None,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "max_uses": max_uses,
            "min_price": str(min_price) if min_price is not None else None,
            "products": product_ids or None,
            "first_consumer_purchase": first_consumer_purchase,
            "combines_with_other_discounts": combines_with_other_discounts,
            "includes_shipping": includes_shipping,
        }
        payload.update({k: v for k, v in optional.items() if v is not None})
        if categories:
            payload["categories"] = await resolve_category_ids(ctx, categories)
        created = await context.run_tiendanube(ctx, lambda: ctx.client.coupons.create(payload))
        await context.record_audit(
            ctx,
            tool_name="create_coupon",
            entity_type="coupon",
            entity_id=created.id,
            before=None,
            after=created.model_dump(mode="json"),
        )
        return summarize(created)

    @mcp.tool(annotations=ToolAnnotations(title="Update coupon", openWorldHint=True))
    async def update_coupon(
        coupon_id: Annotated[int | None, Field(gt=0)] = None,
        code: Annotated[str | None, Field(description="Current code, to find it.")] = None,
        new_code: str | None = None,
        type: CouponType | None = None,
        value: Annotated[Decimal | None, Field(gt=0)] = None,
        start_date: date | None = None,
        end_date: date | None = None,
        max_uses: Annotated[int | None, Field(gt=0)] = None,
        min_price: Annotated[Decimal | None, Field(gt=0)] = None,
        categories: list[CategoryRef] | None = None,
        product_ids: list[int] | None = None,
        first_consumer_purchase: bool | None = None,
        combines_with_other_discounts: bool | None = None,
        includes_shipping: bool | None = None,
    ) -> CouponSummary:
        """Edit a coupon (found by id or code). Only the fields you send change.
        To extend a coupon set a new `end_date`.
        """
        ctx = await context.get_store_context()
        current = await find_coupon(ctx, coupon_id, code)
        effective_type = type or current.type
        check_rules(
            effective_type,
            value if value is not None else current.value,
            start_date,
            end_date,
            bool(categories),
            bool(product_ids),
        )
        # Tiendanube's PUT example sends code/type/value together: keep them consistent.
        payload: dict[str, Any] = {
            "code": normalize_code(new_code) if new_code else current.code,
            "type": effective_type,
        }
        if effective_type != "shipping":
            chosen = value if value is not None else current.value
            if chosen is not None:
                payload["value"] = str(chosen)
        optional: dict[str, Any] = {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "max_uses": max_uses,
            "min_price": str(min_price) if min_price is not None else None,
            "products": product_ids,
            "first_consumer_purchase": first_consumer_purchase,
            "combines_with_other_discounts": combines_with_other_discounts,
            "includes_shipping": includes_shipping,
        }
        payload.update({k: v for k, v in optional.items() if v is not None})
        if categories is not None:
            payload["categories"] = await resolve_category_ids(ctx, categories)
        updated = await context.run_tiendanube(
            ctx, lambda: ctx.client.coupons.update(current.id, payload)
        )
        await context.record_audit(
            ctx,
            tool_name="update_coupon",
            entity_type="coupon",
            entity_id=current.id,
            before=current.model_dump(mode="json"),
            after=updated.model_dump(mode="json"),
        )
        return summarize(updated)

    @mcp.tool(
        annotations=ToolAnnotations(title="Delete coupon", destructiveHint=True, openWorldHint=True)
    )
    async def delete_coupon(
        coupon_id: Annotated[int | None, Field(gt=0)] = None,
        code: str | None = None,
    ) -> CouponDeleted:
        """Delete a coupon (by id or code). Buyers won't be able to use it anymore."""
        ctx = await context.get_store_context()
        current = await find_coupon(ctx, coupon_id, code)
        await context.run_tiendanube(ctx, lambda: ctx.client.coupons.delete(current.id))
        await context.record_audit(
            ctx,
            tool_name="delete_coupon",
            entity_type="coupon",
            entity_id=current.id,
            before=current.model_dump(mode="json"),
            after=None,
        )
        return CouponDeleted(id=current.id, code=current.code, deleted=True)
