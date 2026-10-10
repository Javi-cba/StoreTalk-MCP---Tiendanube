"""Pydantic models for Tiendanube responses (only the fields we use).

Docs: https://tiendanube.github.io/api-documentation/resources/product
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict

LocalizedText = dict[str, str]


def localize(value: LocalizedText | str | None, language: str | None) -> str | None:
    """Collapse multi-language fields ({'es': ..., 'pt': ...}) to the store language."""
    if value is None or isinstance(value, str):
        return value
    if language and value.get(language):
        return value[language]
    return next((v for v in value.values() if v), None)


class _TNModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class TNVariant(_TNModel):
    id: int
    sku: str | None = None
    price: Decimal | None = None
    promotional_price: Decimal | None = None
    stock: int | None = None  # null = infinite stock
    values: list[LocalizedText] = []
    product_id: int | None = None
    image_id: int | None = None
    weight: Decimal | None = None  # kg
    width: Decimal | None = None  # cm
    height: Decimal | None = None
    depth: Decimal | None = None
    cost: Decimal | None = None
    barcode: str | None = None


class TNCategory(_TNModel):
    """https://tiendanube.github.io/api-documentation/resources/category"""

    id: int
    name: LocalizedText | str | None = None
    description: LocalizedText | str | None = None
    handle: LocalizedText | str | None = None
    parent: int | None = None
    subcategories: list[int] = []
    visibility: str | None = None


class TNImage(_TNModel):
    """https://tiendanube.github.io/api-documentation/resources/product-image"""

    id: int
    src: str
    position: int | None = None
    alt: LocalizedText | str | list[Any] | None = None


class TNProduct(_TNModel):
    id: int
    name: LocalizedText | str | None = None
    handle: LocalizedText | str | None = None
    description: LocalizedText | str | None = None
    attributes: list[LocalizedText] = []
    published: bool | None = None
    visibility: str | None = None
    free_shipping: bool | None = None
    requires_shipping: bool | None = None
    brand: str | None = None
    tags: str | None = None
    seo_title: LocalizedText | str | None = None
    seo_description: LocalizedText | str | None = None
    video_url: str | None = None
    variants: list[TNVariant] = []
    categories: list[TNCategory] = []
    images: list[TNImage] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TNStore(_TNModel):
    """GET /store — https://tiendanube.github.io/api-documentation/resources/store"""

    id: int
    name: LocalizedText | str | None = None
    main_language: str | None = None
    main_currency: str | None = None
    original_domain: str | None = None
    url_with_protocol: str | None = None
    email: str | None = None
    logo: str | None = None
    country: str | None = None
    plan_name: str | None = None


class TNCoupon(_TNModel):
    """https://tiendanube.github.io/api-documentation/resources/coupon"""

    id: int
    code: str
    type: str
    value: Decimal | None = None
    valid: bool | None = None
    used: int | None = None
    max_uses: int | None = None
    min_price: Decimal | None = None
    start_date: str | None = None
    end_date: str | None = None
    includes_shipping: bool | None = None
    first_consumer_purchase: bool | None = None
    combines_with_other_discounts: bool | None = None
    categories: list[Any] | None = None
    products: list[Any] | None = None


class TNOrderLine(_TNModel):
    product_id: int | None = None
    variant_id: int | None = None
    name: str | None = None
    sku: str | None = None
    quantity: int | None = None
    price: Decimal | None = None


class TNOrderCustomer(_TNModel):
    id: int | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None


class TNOrder(_TNModel):
    """https://tiendanube.github.io/api-documentation/resources/order"""

    id: int
    number: int | None = None
    status: str | None = None
    payment_status: str | None = None
    shipping_status: str | None = None
    currency: str | None = None
    subtotal: Decimal | None = None
    discount: Decimal | None = None
    total: Decimal | None = None
    coupon: list[dict[str, Any]] | None = None
    gateway_name: str | None = None
    shipping_option: str | None = None
    owner_note: str | None = None
    note: str | None = None
    cancel_reason: str | None = None
    customer: TNOrderCustomer | None = None
    products: list[TNOrderLine] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None
    paid_at: datetime | None = None
    closed_at: datetime | None = None
    cancelled_at: datetime | None = None


class TNPage(_TNModel):
    items: list[dict[str, Any]]
    total: int | None
    has_more: bool
