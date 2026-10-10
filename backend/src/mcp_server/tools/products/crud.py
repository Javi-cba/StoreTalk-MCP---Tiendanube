"""Product tools: list, get, create, update, delete."""

from datetime import datetime
from decimal import Decimal
from functools import partial
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from src.mcp_server import context
from src.mcp_server.context import StoreContext
from src.mcp_server.tools.categories.resolver import CategoryRef, resolve_category_ids
from src.mcp_server.tools.common import i18n, normalize
from src.mcp_server.tools.products.image_input import ImageInput, to_payload
from src.mcp_server.tools.products.schemas import ProductDetail, product_detail
from src.mcp_server.tools.products.variant_rules import normalize_value
from src.services.tiendanube.models import TNProduct, localize
from src.services.tiendanube.resources.products import MAX_ATTRIBUTES, MAX_IMAGES_ON_CREATE

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

Price = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]


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


class ProductDeleted(BaseModel):
    id: int
    name: str | None
    deleted: bool


class NewProductVariant(BaseModel):
    values: Annotated[
        dict[str, str],
        Field(description="Attribute -> value, e.g. {'Color': 'Rojo', 'Talle': 'M'}."),
    ]
    price: Price | None = None
    promotional_price: Price | None = None
    stock: Annotated[int | None, Field(ge=0, description="Omit for unlimited stock.")] = None
    sku: str | None = None


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


def _variant_fields(
    *,
    price: Decimal | None,
    promotional_price: Decimal | None,
    stock: int | None,
    sku: str | None,
    cost: Decimal | None = None,
    weight: Decimal | None = None,
    width: Decimal | None = None,
    height: Decimal | None = None,
    depth: Decimal | None = None,
    barcode: str | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "price": price,
        "promotional_price": promotional_price,
        "stock": stock,
        "sku": sku,
        "cost": cost,
        "weight": weight,
        "width": width,
        "height": height,
        "depth": depth,
        "barcode": barcode,
    }
    return {k: str(v) if isinstance(v, Decimal) else v for k, v in data.items() if v is not None}


def _build_variants(
    variants: list[NewProductVariant], base: dict[str, Any], language: str | None
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    """Attributes are inferred from the value keys, in order of first appearance."""
    attributes: list[str] = []
    for variant in variants:
        for key in variant.values:
            if not any(normalize(key) == normalize(a) for a in attributes):
                attributes.append(key.strip())
    if len(attributes) > MAX_ATTRIBUTES:
        raise ToolError(
            f"Tiendanube permite hasta {MAX_ATTRIBUTES} atributos por producto "
            f"(recibí {len(attributes)}: {', '.join(attributes)})."
        )
    seen_values: dict[int, list[str]] = {i: [] for i in range(len(attributes))}
    payloads: list[dict[str, Any]] = []
    for variant in variants:
        by_attr = {normalize(k): v for k, v in variant.values.items()}
        values: list[dict[str, str]] = []
        for i, attribute in enumerate(attributes):
            raw = by_attr.get(normalize(attribute))
            if not raw:
                raise ToolError(
                    f"Todas las variantes tienen que indicar '{attribute}' "
                    f"(falta en {variant.values})."
                )
            value = normalize_value(attribute, raw, seen_values[i])
            seen_values[i].append(value)
            values.append(i18n(value, language))
        payload = {
            **base,
            **_variant_fields(
                price=variant.price,
                promotional_price=variant.promotional_price,
                stock=variant.stock,
                sku=variant.sku,
            ),
            "values": values,
        }
        if variant.stock is None and "stock" not in base:
            payload["stock"] = ""  # unlimited
        payloads.append(payload)
    return [i18n(a, language) for a in attributes], payloads


async def _find_product(ctx: StoreContext, product_id: int | None, sku: str | None) -> TNProduct:
    if product_id is not None:
        return await context.run_tiendanube(ctx, lambda: ctx.client.products.get(product_id))
    if sku:
        found = await context.run_tiendanube(ctx, lambda: ctx.client.products.get_by_sku(sku))
        if found is None:
            raise ToolError(f"No existe ningún producto con el SKU '{sku}'.")
        return found
    raise ToolError("Indicá el id del producto o un SKU. Usá list_products para buscarlo.")


async def _upload_images(
    ctx: StoreContext, product_id: int, images: list[ImageInput]
) -> tuple[int, list[str]]:
    """Upload one by one so a bad image doesn't lose the others. POSTs are never retried."""
    uploaded, warnings = 0, []
    for index, image in enumerate(images, start=1):
        try:
            payload = to_payload(image, ctx.language)
            await context.run_tiendanube(
                ctx, partial(ctx.client.images.create, product_id, payload)
            )
            uploaded += 1
        except ToolError as exc:
            warnings.append(f"Imagen {index} no se cargó: {exc}")
    return uploaded, warnings


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
        ctx = await context.get_store_context()
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
        result = await context.run_tiendanube(ctx, lambda: ctx.client.products.list(params))
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

    @mcp.tool(
        annotations=ToolAnnotations(title="Get product", readOnlyHint=True, openWorldHint=True)
    )
    async def get_product(
        product_id: Annotated[int | None, Field(gt=0, description="Product id.")] = None,
        sku: Annotated[str | None, Field(description="SKU of any of its variants.")] = None,
    ) -> ProductDetail:
        """Full detail of one product: description, SEO, tags, attributes, every variant
        (values, price, stock, SKU, ids), categories and images (ids, position).

        Use it before editing variants or images to get their ids.
        """
        ctx = await context.get_store_context()
        product = await _find_product(ctx, product_id, sku)
        return product_detail(product, ctx.language)

    @mcp.tool(annotations=ToolAnnotations(title="Create product", openWorldHint=True))
    async def create_product(
        name: Annotated[str, Field(min_length=1, max_length=255)],
        price: Annotated[
            Price | None, Field(description="Price (all variants unless overridden).")
        ] = None,
        promotional_price: Annotated[
            Price | None, Field(description="Sale price, lower than `price`.")
        ] = None,
        stock: Annotated[
            int | None, Field(ge=0, description="Stock. Omit for unlimited stock.")
        ] = None,
        sku: Annotated[str | None, Field(description="SKU (only without variants).")] = None,
        cost: Annotated[Price | None, Field(description="Unit cost (for margins).")] = None,
        description: Annotated[str | None, Field(description="Description (HTML allowed).")] = None,
        variants: Annotated[
            list[NewProductVariant] | None,
            Field(
                description="Variants, e.g. [{'values': {'Talle': 'S'}}, "
                "{'values': {'Talle': 'M'}, 'stock': 3}]. Attributes are inferred from the "
                "keys (max 3). Each variant inherits price/stock/cost unless it sets its own."
            ),
        ] = None,
        categories: Annotated[
            list[CategoryRef] | None,
            Field(description="Category names ('Remeras', 'Hombre > Remeras') or ids."),
        ] = None,
        create_missing_categories: Annotated[
            bool, Field(description="Create categories that don't exist yet.")
        ] = False,
        images: Annotated[
            list[ImageInput] | None,
            Field(description="Images by URL or base64 (JPG, PNG, GIF, WEBP; < 10MB)."),
        ] = None,
        brand: str | None = None,
        tags: Annotated[list[str] | None, Field(description="Search tags.")] = None,
        published: Annotated[bool, Field(description="Visible in the store.")] = True,
        free_shipping: bool | None = None,
        requires_shipping: Annotated[
            bool | None, Field(description="false for digital products / services.")
        ] = None,
        weight: Annotated[Decimal | None, Field(ge=0, description="Weight in kg.")] = None,
        width: Annotated[Decimal | None, Field(ge=0, description="Width in cm.")] = None,
        height: Annotated[Decimal | None, Field(ge=0, description="Height in cm.")] = None,
        depth: Annotated[Decimal | None, Field(ge=0, description="Depth in cm.")] = None,
        seo_title: Annotated[str | None, Field(max_length=70)] = None,
        seo_description: Annotated[str | None, Field(max_length=320)] = None,
        video_url: Annotated[str | None, Field(description="https URL (YouTube/Vimeo).")] = None,
    ) -> ProductDetail:
        """Create a product, optionally with variants, categories and images.

        Without `variants` it is created as a single product with `price`/`stock`/`sku`.
        Images accept a public URL (preferred) or base64.
        """
        if promotional_price is not None and price is not None and promotional_price >= price:
            raise ToolError("El precio promocional tiene que ser menor al precio.")
        if video_url and not video_url.startswith("https://"):
            raise ToolError("La URL del video tiene que empezar con https://.")
        ctx = await context.get_store_context()
        lang = ctx.language
        category_ids = await resolve_category_ids(
            ctx, categories or [], create_missing=create_missing_categories
        )

        base = _variant_fields(
            price=price,
            promotional_price=promotional_price,
            stock=stock,
            sku=None,
            cost=cost,
            weight=weight,
            width=width,
            height=height,
            depth=depth,
        )
        payload: dict[str, Any] = {"name": i18n(name.strip(), lang), "published": published}
        if variants:
            attributes, variant_payloads = _build_variants(variants, base, lang)
            payload["attributes"] = attributes
            payload["variants"] = variant_payloads
        else:
            single = {**base, **({"sku": sku} if sku else {})}
            if stock is None:
                single["stock"] = ""  # unlimited
            payload["variants"] = [single]
        optional: dict[str, Any] = {
            "description": i18n(description, lang) if description else None,
            "brand": brand,
            "tags": ",".join(t.strip() for t in tags) if tags else None,
            "free_shipping": free_shipping,
            "requires_shipping": requires_shipping,
            "seo_title": i18n(seo_title, lang) if seo_title else None,
            "seo_description": i18n(seo_description, lang) if seo_description else None,
            "video_url": video_url,
            "categories": category_ids or None,
        }
        payload.update({k: v for k, v in optional.items() if v is not None})

        # URL images go inline (max 9 per docs); base64 and the rest are uploaded after.
        images = images or []
        for image in images:
            to_payload(image, lang)  # validate everything before creating the product
        inline = [i for i in images if i.url][:MAX_IMAGES_ON_CREATE]
        later = [i for i in images if i not in inline]
        if inline:
            payload["images"] = [to_payload(i, lang) for i in inline]

        created = await context.run_tiendanube(ctx, lambda: ctx.client.products.create(payload))
        warnings: list[str] = []
        if later:
            _, warnings = await _upload_images(ctx, created.id, later)
            created = await context.run_tiendanube(ctx, lambda: ctx.client.products.get(created.id))
        await context.record_audit(
            ctx,
            tool_name="create_product",
            entity_type="product",
            entity_id=created.id,
            before=None,
            after=created.model_dump(mode="json"),
        )
        return product_detail(created, lang, warnings)

    @mcp.tool(annotations=ToolAnnotations(title="Update product", openWorldHint=True))
    async def update_product(
        product_id: Annotated[int, Field(gt=0)],
        name: Annotated[str | None, Field(min_length=1, max_length=255)] = None,
        description: str | None = None,
        price: Annotated[
            Price | None, Field(description="New price for ALL the product's variants.")
        ] = None,
        promotional_price: Annotated[
            Price | None, Field(description="New sale price for ALL variants.")
        ] = None,
        remove_promotional_price: Annotated[
            bool, Field(description="Remove the sale price from all variants.")
        ] = False,
        stock: Annotated[
            int | None, Field(ge=0, description="New stock for ALL variants (per variant).")
        ] = None,
        cost: Annotated[Price | None, Field(description="Unit cost for ALL variants.")] = None,
        categories: Annotated[
            list[CategoryRef] | None,
            Field(description="Replace the categories (names, paths or ids). [] removes all."),
        ] = None,
        add_categories: Annotated[
            list[CategoryRef] | None, Field(description="Categories to add, keeping the rest.")
        ] = None,
        remove_categories: Annotated[
            list[CategoryRef] | None, Field(description="Categories to remove.")
        ] = None,
        create_missing_categories: bool = False,
        brand: str | None = None,
        tags: Annotated[list[str] | None, Field(description="Replace all tags.")] = None,
        add_tags: Annotated[list[str] | None, Field(description="Tags to add.")] = None,
        published: Annotated[bool | None, Field(description="Show/hide in the store.")] = None,
        free_shipping: bool | None = None,
        requires_shipping: bool | None = None,
        seo_title: Annotated[str | None, Field(max_length=70)] = None,
        seo_description: Annotated[str | None, Field(max_length=320)] = None,
        video_url: str | None = None,
    ) -> ProductDetail:
        """Edit a product. Only the fields you send change.

        `price`, `promotional_price`, `stock` and `cost` apply to every variant: to change
        one variant (e.g. only size L) use update_variant. To raise prices by a
        percentage use adjust_prices_by_category.
        """
        if video_url and not video_url.startswith("https://"):
            raise ToolError("La URL del video tiene que empezar con https://.")
        ctx = await context.get_store_context()
        lang = ctx.language
        before = await context.run_tiendanube(ctx, lambda: ctx.client.products.get(product_id))

        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = i18n(name.strip(), lang)
        if description is not None:
            payload["description"] = i18n(description, lang)
        if brand is not None:
            payload["brand"] = brand
        if published is not None:
            payload["published"] = published
        if free_shipping is not None:
            payload["free_shipping"] = free_shipping
        if requires_shipping is not None:
            payload["requires_shipping"] = requires_shipping
        if seo_title is not None:
            payload["seo_title"] = i18n(seo_title, lang)
        if seo_description is not None:
            payload["seo_description"] = i18n(seo_description, lang)
        if video_url is not None:
            payload["video_url"] = video_url
        if tags is not None or add_tags:
            current = (
                []
                if tags is not None
                else [t.strip() for t in (before.tags or "").split(",") if t.strip()]
            )
            merged = current + [t for t in (tags or []) + (add_tags or []) if t not in current]
            payload["tags"] = ",".join(merged)
        if categories is not None or add_categories or remove_categories:
            ids = (
                await resolve_category_ids(
                    ctx, categories, create_missing=create_missing_categories
                )
                if categories is not None
                else [c.id for c in before.categories]
            )
            ids += [
                i
                for i in await resolve_category_ids(
                    ctx, add_categories or [], create_missing=create_missing_categories
                )
                if i not in ids
            ]
            removed = set(await resolve_category_ids(ctx, remove_categories or []))
            payload["categories"] = [i for i in ids if i not in removed]

        variant_changes = _variant_fields(
            price=price, promotional_price=promotional_price, stock=stock, sku=None, cost=cost
        )
        if remove_promotional_price:
            variant_changes["promotional_price"] = None
        if (
            "promotional_price" in variant_changes
            and variant_changes["promotional_price"] is not None
        ):
            prices = [price] if price is not None else [v.price for v in before.variants]
            if any(
                p is not None and Decimal(variant_changes["promotional_price"]) >= p for p in prices
            ):
                raise ToolError("El precio promocional tiene que ser menor al precio.")
        if not payload and not variant_changes:
            raise ToolError("No indicaste ningún cambio para el producto.")

        if payload:
            await context.run_tiendanube(
                ctx, lambda: ctx.client.products.update(product_id, payload)
            )
        if variant_changes:
            items = [{"id": v.id, **variant_changes} for v in before.variants]
            await context.run_tiendanube(
                ctx, lambda: ctx.client.variants.patch_many(product_id, items)
            )
        after = await context.run_tiendanube(ctx, lambda: ctx.client.products.get(product_id))
        await context.record_audit(
            ctx,
            tool_name="update_product",
            entity_type="product",
            entity_id=product_id,
            before=before.model_dump(mode="json"),
            after=after.model_dump(mode="json"),
        )
        return product_detail(after, lang)

    @mcp.tool(
        annotations=ToolAnnotations(
            title="Delete product", destructiveHint=True, openWorldHint=True
        )
    )
    async def delete_product(product_id: Annotated[int, Field(gt=0)]) -> ProductDeleted:
        """Delete a product with all its variants and images. Cannot be undone.

        Confirm the product name with the user before calling it. To just hide it from the
        store use update_product(published=false).
        """
        ctx = await context.get_store_context()
        before = await context.run_tiendanube(ctx, lambda: ctx.client.products.get(product_id))
        await context.run_tiendanube(ctx, lambda: ctx.client.products.delete(product_id))
        await context.record_audit(
            ctx,
            tool_name="delete_product",
            entity_type="product",
            entity_id=product_id,
            before=before.model_dump(mode="json"),
            after=None,
        )
        return ProductDeleted(id=product_id, name=localize(before.name, ctx.language), deleted=True)
