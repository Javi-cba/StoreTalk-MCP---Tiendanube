"""Output models of the coupon tools."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from src.services.tiendanube.models import TNCoupon

COUPON_FIELDS = (
    "id,code,type,value,valid,used,max_uses,min_price,start_date,end_date,"
    "includes_shipping,first_consumer_purchase,combines_with_other_discounts,categories,products"
)


class CouponSummary(BaseModel):
    id: int
    code: str
    type: str = Field(description="percentage | absolute (fixed amount) | shipping (free).")
    value: Decimal | None
    valid: bool | None
    used: int | None
    max_uses: int | None
    min_price: Decimal | None
    start_date: str | None
    end_date: str | None
    includes_shipping: bool | None
    first_consumer_purchase: bool | None
    combines_with_other_discounts: bool | None
    category_ids: list[int]
    product_ids: list[int]


class CouponListResult(BaseModel):
    coupons: list[CouponSummary]
    page: int
    total: int | None
    has_more: bool


class CouponDeleted(BaseModel):
    id: int
    code: str
    deleted: bool


def _ids(items: list[Any] | None) -> list[int]:
    result = []
    for item in items or []:
        value = item.get("id") if isinstance(item, dict) else getattr(item, "id", item)
        if isinstance(value, int):
            result.append(value)
    return result


def summarize(coupon: TNCoupon) -> CouponSummary:
    return CouponSummary(
        id=coupon.id,
        code=coupon.code,
        type=coupon.type,
        value=coupon.value,
        valid=coupon.valid,
        used=coupon.used,
        max_uses=coupon.max_uses,
        min_price=coupon.min_price,
        start_date=coupon.start_date,
        end_date=coupon.end_date,
        includes_shipping=coupon.includes_shipping,
        first_consumer_purchase=coupon.first_consumer_purchase,
        combines_with_other_discounts=coupon.combines_with_other_discounts,
        category_ids=_ids(coupon.categories),
        product_ids=_ids(coupon.products),
    )
