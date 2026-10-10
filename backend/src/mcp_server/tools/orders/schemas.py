"""Output models of the order tools."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from src.mcp_server.context import StoreContext
from src.services.tiendanube.models import TNOrder
from src.services.tiendanube.scopes import Scope, is_granted

OrderStatus = Literal["any", "open", "closed", "cancelled"]
PaymentStatus = Literal["any", "pending", "authorized", "paid", "abandoned", "refunded", "voided"]
ShippingStatus = Literal["any", "unpacked", "unfulfilled", "fulfilled"]

LIST_FIELDS = (
    "id,number,status,payment_status,shipping_status,currency,total,created_at,customer,products"
)


class OrderLine(BaseModel):
    product_id: int | None
    variant_id: int | None
    name: str | None
    sku: str | None
    quantity: int | None
    price: Decimal | None


class OrderSummary(BaseModel):
    id: int
    number: int | None = Field(description="Number the buyer sees (#1234).")
    status: str | None
    payment_status: str | None
    shipping_status: str | None
    total: Decimal | None
    currency: str | None
    customer_name: str | None = Field(description="null if the app lacks read_customers.")
    items_count: int
    created_at: datetime | None


class OrderDetail(OrderSummary):
    subtotal: Decimal | None
    discount: Decimal | None
    coupons: list[str]
    payment_method: str | None
    shipping_option: str | None
    customer_email: str | None
    customer_phone: str | None
    buyer_note: str | None
    owner_note: str | None
    cancel_reason: str | None
    products: list[OrderLine]
    paid_at: datetime | None
    closed_at: datetime | None
    cancelled_at: datetime | None
    notes: list[str] = []


class OrderListResult(BaseModel):
    orders: list[OrderSummary]
    page: int
    total: int | None
    has_more: bool


def order_summary(order: TNOrder) -> OrderSummary:
    return OrderSummary(
        id=order.id,
        number=order.number,
        status=order.status,
        payment_status=order.payment_status,
        shipping_status=order.shipping_status,
        total=order.total,
        currency=order.currency,
        customer_name=order.customer.name if order.customer else None,
        items_count=sum(p.quantity or 0 for p in order.products),
        created_at=order.created_at,
    )


def order_detail(order: TNOrder, ctx: StoreContext) -> OrderDetail:
    notes = []
    granted = ctx.client.granted_scopes
    if granted and not is_granted(Scope.READ_CUSTOMERS, granted):
        notes.append(
            "Los datos del comprador no se muestran porque falta el permiso `read_customers`; "
            "se puede agregar desde el admin de StoreTalk."
        )
    customer = order.customer
    return OrderDetail(
        **order_summary(order).model_dump(),
        subtotal=order.subtotal,
        discount=order.discount,
        coupons=[str(c.get("code")) for c in order.coupon or [] if c.get("code")],
        payment_method=order.gateway_name,
        shipping_option=order.shipping_option,
        customer_email=customer.email if customer else None,
        customer_phone=customer.phone if customer else None,
        buyer_note=order.note,
        owner_note=order.owner_note,
        cancel_reason=order.cancel_reason,
        products=[OrderLine(**line.model_dump()) for line in order.products],
        paid_at=order.paid_at,
        closed_at=order.closed_at,
        cancelled_at=order.cancelled_at,
        notes=notes,
    )
