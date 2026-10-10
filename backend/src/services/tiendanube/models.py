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


class TNCategory(_TNModel):
    id: int
    name: LocalizedText | str | None = None


class TNImage(_TNModel):
    id: int
    src: str


class TNProduct(_TNModel):
    id: int
    name: LocalizedText | str | None = None
    handle: LocalizedText | str | None = None
    published: bool | None = None
    free_shipping: bool | None = None
    brand: str | None = None
    variants: list[TNVariant] = []
    categories: list[TNCategory] = []
    images: list[TNImage] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TNStore(_TNModel):
    id: int
    name: LocalizedText | str | None = None
    main_language: str | None = None
    original_domain: str | None = None
    email: str | None = None


class TNPage(_TNModel):
    items: list[dict[str, Any]]
    total: int | None
    has_more: bool
