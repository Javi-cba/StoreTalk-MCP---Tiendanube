"""Output models shared by the product, variant and image tools."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.services.tiendanube.models import TNProduct, TNVariant, localize


class VariantSummary(BaseModel):
    id: int
    values: dict[str, str] = Field(description="Attribute -> value, e.g. {'Talle': 'L'}.")
    sku: str | None
    price: Decimal | None
    promotional_price: Decimal | None
    stock: int | None = Field(description="null = unlimited stock.")
    cost: Decimal | None = None
    weight: Decimal | None = None
    barcode: str | None = None
    image_id: int | None = None


class ImageSummary(BaseModel):
    id: int
    src: str
    position: int | None


class CategoryRefOut(BaseModel):
    id: int
    name: str | None


class ProductDetail(BaseModel):
    id: int
    name: str | None
    handle: str | None
    description: str | None
    published: bool | None
    visibility: str | None
    brand: str | None
    tags: list[str]
    free_shipping: bool | None
    requires_shipping: bool | None
    seo_title: str | None
    seo_description: str | None
    video_url: str | None
    attributes: list[str] = Field(description="Variant attribute names, e.g. ['Color', 'Talle'].")
    variants: list[VariantSummary]
    categories: list[CategoryRefOut]
    images: list[ImageSummary]
    created_at: datetime | None
    updated_at: datetime | None
    warnings: list[str] = []


def attribute_names(product: TNProduct, language: str | None) -> list[str]:
    return [localize(a, language) or f"Atributo {i + 1}" for i, a in enumerate(product.attributes)]


def variant_values(variant: TNVariant, language: str | None) -> list[str]:
    return [localize(v, language) or "" for v in variant.values]


def summarize_variant(
    variant: TNVariant, attributes: list[str], language: str | None
) -> VariantSummary:
    values = variant_values(variant, language)
    return VariantSummary(
        id=variant.id,
        values=dict(zip(attributes, values, strict=False)),
        sku=variant.sku,
        price=variant.price,
        promotional_price=variant.promotional_price,
        stock=variant.stock,
        cost=variant.cost,
        weight=variant.weight,
        barcode=variant.barcode,
        image_id=variant.image_id,
    )


def product_detail(
    product: TNProduct, language: str | None, warnings: list[str] | None = None
) -> ProductDetail:
    attributes = attribute_names(product, language)
    return ProductDetail(
        id=product.id,
        name=localize(product.name, language),
        handle=localize(product.handle, language),
        description=localize(product.description, language),
        published=product.published,
        visibility=product.visibility,
        brand=product.brand,
        tags=[t.strip() for t in (product.tags or "").split(",") if t.strip()],
        free_shipping=product.free_shipping,
        requires_shipping=product.requires_shipping,
        seo_title=localize(product.seo_title, language),
        seo_description=localize(product.seo_description, language),
        video_url=product.video_url,
        attributes=attributes,
        variants=[summarize_variant(v, attributes, language) for v in product.variants],
        categories=[
            CategoryRefOut(id=c.id, name=localize(c.name, language)) for c in product.categories
        ],
        images=[ImageSummary(id=i.id, src=i.src, position=i.position) for i in product.images],
        created_at=product.created_at,
        updated_at=product.updated_at,
        warnings=warnings or [],
    )
