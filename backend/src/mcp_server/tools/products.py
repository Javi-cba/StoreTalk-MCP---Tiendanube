from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from src.mcp_server.context import get_store_context, run_tiendanube
from src.services.tiendanube.models import TNProduct, localize

SortBy = Literal[
    "user",
    "price-ascending",
    "price-descending",
    "alpha-ascending",
    "alpha-descending",
    "created-at-ascending",
    "created-at-descending",
    "best-selling",
]

# Only what list_products returns; the rest of the product payload is never requested.
_PRODUCT_FIELDS = (
    "id,name,handle,published,free_shipping,brand,variants,categories,images,created_at,updated_at"
)
_MAX_SKUS = 5


class ProductSummary(BaseModel):
    id: int
    name: str | None
    handle: str | None
    published: bool | None
    brand: str | None
    price_min: Decimal | None
    price_max: Decimal | None
    on_promotion: bool
    stock_total: int | None = Field(
        description="Sum of variant stock. null = at least one variant has unlimited stock."
    )
    variants_count: int
    skus: list[str]
    categories: list[str]
    image_url: str | None
    updated_at: datetime | None


class ProductListResult(BaseModel):
    products: list[ProductSummary]
    page: int
    per_page: int
    total: int | None
    has_more: bool


def _summarize(product: TNProduct, language: str | None) -> ProductSummary:
    prices = [v.price for v in product.variants if v.price is not None]
    stocks = [v.stock for v in product.variants]
    return ProductSummary(
        id=product.id,
        name=localize(product.name, language),
        handle=localize(product.handle, language),
        published=product.published,
        brand=product.brand,
        price_min=min(prices) if prices else None,
        price_max=max(prices) if prices else None,
        on_promotion=any(v.promotional_price is not None for v in product.variants),
        stock_total=None if any(s is None for s in stocks) else sum(s for s in stocks if s),
        variants_count=len(product.variants),
        skus=[v.sku for v in product.variants if v.sku][:_MAX_SKUS],
        categories=[n for c in product.categories if (n := localize(c.name, language))],
        image_url=product.images[0].src if product.images else None,
        updated_at=product.updated_at,
    )


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(title="List products", readOnlyHint=True, openWorldHint=True),
    )
    async def list_products(
        q: Annotated[
            str | None, Field(description="Text search over product name, tags or SKU.")
        ] = None,
        category_id: Annotated[int | None, Field(gt=0, description="Only this category.")] = None,
        published: Annotated[
            bool | None,
            Field(description="true = visible in the store, false = hidden/unlisted."),
        ] = None,
        min_stock: Annotated[int | None, Field(ge=0, description="Minimum stock.")] = None,
        max_stock: Annotated[
            int | None, Field(ge=0, description="Maximum stock (use 0 for out of stock).")
        ] = None,
        has_promotional_price: Annotated[
            bool | None, Field(description="Only products with/without a promotional price.")
        ] = None,
        free_shipping: Annotated[bool | None, Field(description="Free shipping status.")] = None,
        created_at_min: Annotated[
            datetime | None, Field(description="Created on or after (ISO 8601).")
        ] = None,
        created_at_max: Annotated[
            datetime | None, Field(description="Created on or before (ISO 8601).")
        ] = None,
        updated_at_min: Annotated[
            datetime | None, Field(description="Updated on or after (ISO 8601).")
        ] = None,
        updated_at_max: Annotated[
            datetime | None, Field(description="Updated on or before (ISO 8601).")
        ] = None,
        sort_by: Annotated[SortBy | None, Field(description="Sort order.")] = None,
        page: Annotated[int, Field(ge=1, description="Page number, starting at 1.")] = 1,
        per_page: Annotated[int, Field(ge=1, le=50, description="Products per page.")] = 20,
    ) -> ProductListResult:
        """List the connected store's products, with optional filters.

        Call without filters to browse the catalog. Use `q` to search by name/tag/SKU,
        `max_stock=0` for out-of-stock products, `published=false` for hidden ones.
        Returns a summary per product (price range, total stock, SKUs, categories) and
        pagination info: if `has_more` is true, call again with `page + 1`.
        """
        ctx = await get_store_context()
        params: dict[str, Any] = {
            "q": q,
            "category_id": category_id,
            "published": published,
            "min_stock": min_stock,
            "max_stock": max_stock,
            "has_promotional_price": has_promotional_price,
            "free_shipping": free_shipping,
            "created_at_min": created_at_min.isoformat() if created_at_min else None,
            "created_at_max": created_at_max.isoformat() if created_at_max else None,
            "updated_at_min": updated_at_min.isoformat() if updated_at_min else None,
            "updated_at_max": updated_at_max.isoformat() if updated_at_max else None,
            "sort_by": sort_by,
            "page": page,
            "per_page": per_page,
            "fields": _PRODUCT_FIELDS,
        }
        result = await run_tiendanube(ctx, lambda: ctx.client.list_products(params))
        products = [
            _summarize(TNProduct.model_validate(item), ctx.language) for item in result.items
        ]
        return ProductListResult(
            products=products,
            page=page,
            per_page=per_page,
            total=result.total,
            has_more=result.has_more,
        )
