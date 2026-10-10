"""Bulk price changes: raise/lower prices by a percentage for a category."""

import asyncio
from decimal import Decimal
from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from src.mcp_server import context
from src.mcp_server.context import StoreContext
from src.mcp_server.tools.categories.resolver import CategoryRef, load_category_index
from src.mcp_server.tools.common import Rounding, apply_percentage
from src.mcp_server.tools.products.schemas import attribute_names, variant_values
from src.services.tiendanube.errors import (
    TiendanubeError,
    TiendanubeNotFoundError,
    TiendanubeValidationError,
)
from src.services.tiendanube.models import TNProduct, localize
from src.services.tiendanube.scopes import Scope, is_granted, missing_scope_message

_PAGE_SIZE = 200
_MAX_PAGES_PER_CATEGORY = 5
_MAX_PRODUCTS = 1000
_PREVIEW_LINES = 30
# Stop writing when less than this is left of the tool deadline and report partial results.
_SAFETY_MARGIN_SECONDS = 4.0


class PriceChange(BaseModel):
    product_id: int
    product: str | None
    variant_id: int
    variant: str
    old_price: Decimal
    new_price: Decimal
    old_promotional_price: Decimal | None = None
    new_promotional_price: Decimal | None = None


class PriceAdjustmentResult(BaseModel):
    dry_run: bool
    category: str
    categories_included: list[str]
    percentage: Decimal
    products_matched: int
    variants_to_change: int
    preview: list[PriceChange] = Field(description=f"First {_PREVIEW_LINES} changes.")
    products_updated: int = 0
    variants_updated: int = 0
    failed: list[str] = []
    completed: bool = Field(description="false = stopped by the time limit: call it again.")
    resume_after_product_id: int | None = Field(
        default=None,
        description="Pass it back to continue exactly where it stopped (avoids double raises).",
    )
    message: str


async def _products_in(ctx: StoreContext, category_ids: list[int]) -> tuple[list[TNProduct], bool]:
    """Products of the categories, filtered by Tiendanube (category_id), deduplicated."""
    products: dict[int, TNProduct] = {}
    truncated = False
    for category_id in category_ids:
        for page in range(1, _MAX_PAGES_PER_CATEGORY + 1):
            result = await ctx.client.products.list(
                {
                    "category_id": category_id,
                    "fields": "id,name,attributes,variants",
                    "page": page,
                    "per_page": _PAGE_SIZE,
                }
            )
            for item in result.items:
                product = TNProduct.model_validate(item)
                products.setdefault(product.id, product)
            if len(products) > _MAX_PRODUCTS:
                return sorted(products.values(), key=lambda p: p.id)[:_MAX_PRODUCTS], True
            if not result.has_more:
                break
        else:
            truncated = True
    return sorted(products.values(), key=lambda p: p.id), truncated


def _changes_for(
    product: TNProduct,
    percentage: Decimal,
    rounding: Rounding,
    include_promotional: bool,
    language: str | None,
) -> list[PriceChange]:
    attributes = attribute_names(product, language)
    changes = []
    for variant in product.variants:
        if variant.price is None:  # "contact us" price: nothing to raise
            continue
        new_promo = None
        if include_promotional and variant.promotional_price is not None:
            new_promo = apply_percentage(variant.promotional_price, percentage, rounding)
        label = ", ".join(
            f"{a}: {v}" for a, v in zip(attributes, variant_values(variant, language), strict=False)
        )
        changes.append(
            PriceChange(
                product_id=product.id,
                product=localize(product.name, language),
                variant_id=variant.id,
                variant=label or "única",
                old_price=variant.price,
                new_price=apply_percentage(variant.price, percentage, rounding),
                old_promotional_price=variant.promotional_price,
                new_promotional_price=new_promo,
            )
        )
    return changes


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="Adjust prices by category", destructiveHint=True, openWorldHint=True
        )
    )
    async def adjust_prices_by_category(
        category: Annotated[
            CategoryRef, Field(description="Category name ('Remeras'), path or id.")
        ],
        percentage: Annotated[
            Decimal,
            Field(
                gt=-90,
                le=500,
                description="Percent change: 10 raises 10%, -15 lowers 15%.",
            ),
        ],
        dry_run: Annotated[
            bool,
            Field(description="true (default) = only preview. false = apply the changes."),
        ] = True,
        include_subcategories: Annotated[
            bool, Field(description="Also change products of its subcategories.")
        ] = True,
        include_promotional_price: Annotated[
            bool, Field(description="Also adjust existing sale prices by the same %.")
        ] = True,
        rounding: Annotated[
            Rounding,
            Field(description="Round new prices: none (cents), integer, tens or hundreds."),
        ] = "none",
        resume_after_product_id: Annotated[
            int | None, Field(gt=0, description="From a previous partial run.")
        ] = None,
    ) -> PriceAdjustmentResult:
        """Raise or lower by a percentage the price of every variant of the products in a
        category, e.g. "+10% to the t-shirts" -> category='Remeras', percentage=10.

        ALWAYS call it first with dry_run=true, show the preview to the user and only after
        their confirmation call it again with dry_run=false. If `completed` is false, call it
        again with the same arguments and `resume_after_product_id`.
        """
        started_at = asyncio.get_running_loop().time()
        ctx = await context.get_store_context()
        lang = ctx.language
        index = await load_category_index(ctx)
        root = index.require(category)
        category_ids = [root.id] + (index.descendants(root.id) if include_subcategories else [])
        products, truncated = await context.run_tiendanube(
            ctx, lambda: _products_in(ctx, category_ids)
        )
        if resume_after_product_id:
            products = [p for p in products if p.id > resume_after_product_id]

        plan = [
            (product, _changes_for(product, percentage, rounding, include_promotional_price, lang))
            for product in products
        ]
        plan = [(p, c) for p, c in plan if c]
        all_changes = [change for _, changes in plan for change in changes]
        base = {
            "category": index.path(root),
            "categories_included": [index.path(index.by_id[i]) for i in category_ids],
            "percentage": percentage,
            "products_matched": len(plan),
            "variants_to_change": len(all_changes),
            "preview": all_changes[:_PREVIEW_LINES],
        }
        if not plan:
            return PriceAdjustmentResult(
                dry_run=dry_run,
                completed=True,
                message="No hay productos con precio en esa categoría.",
                **base,
            )
        warning = (
            f" Atención: la categoría tiene más de {_MAX_PRODUCTS} productos; se procesan los "
            "primeros y después hay que volver a llamar con resume_after_product_id."
            if truncated
            else ""
        )
        if dry_run:
            granted = ctx.client.granted_scopes
            if granted and not is_granted(Scope.WRITE_PRODUCTS, granted):
                warning += " " + missing_scope_message(Scope.WRITE_PRODUCTS)
            return PriceAdjustmentResult(
                dry_run=True,
                completed=False,
                message=(
                    f"Vista previa: {len(all_changes)} variantes de {len(plan)} productos. "
                    "Confirmá con el usuario y llamá de nuevo con dry_run=false." + warning
                ),
                **base,
            )

        updated_products = updated_variants = 0
        failed: list[str] = []
        audit_before: dict[str, Any] = {}
        audit_after: dict[str, Any] = {}
        last_done: int | None = None
        for product, changes in plan:
            if context.remaining_budget(started_at) < _SAFETY_MARGIN_SECONDS:
                break
            items: list[dict[str, Any]] = []
            for change in changes:
                item: dict[str, Any] = {"id": change.variant_id, "price": str(change.new_price)}
                if change.new_promotional_price is not None:
                    item["promotional_price"] = str(change.new_promotional_price)
                items.append(item)
            try:
                # One PATCH per product updates all its variants in a single request.
                await ctx.client.variants.patch_many(product.id, items)
            except (TiendanubeValidationError, TiendanubeNotFoundError) as exc:
                failed.append(f"{localize(product.name, lang)} (id {product.id}): {exc.message}")
            except TiendanubeError as exc:
                # Auth / scope / outage: stop here, everything before was applied.
                failed.append(f"Se detuvo en el producto {product.id}: {exc.message}")
                break
            else:
                updated_products += 1
                updated_variants += len(items)
                for change in changes:
                    key = str(change.variant_id)
                    audit_before[key] = [str(change.old_price), str(change.old_promotional_price)]
                    audit_after[key] = [str(change.new_price), str(change.new_promotional_price)]
            last_done = product.id

        completed = last_done == plan[-1][0].id and not truncated
        if audit_after:
            await context.record_audit(
                ctx,
                tool_name="adjust_prices_by_category",
                entity_type="category",
                entity_id=root.id,
                before={"percentage": str(percentage), "variants": audit_before},
                after={"variants": audit_after},
            )
        message = f"Se actualizaron {updated_variants} variantes de {updated_products} productos."
        if failed:
            message += f" Fallaron {len(failed)}."
        if not completed:
            message += (
                " No llegó a terminar dentro del tiempo límite: volvé a llamar con "
                f"dry_run=false y resume_after_product_id={last_done}."
            )
        if not updated_products and failed:
            raise ToolError(message + " " + "; ".join(failed[:5]))
        return PriceAdjustmentResult(
            dry_run=False,
            products_updated=updated_products,
            variants_updated=updated_variants,
            failed=failed,
            completed=completed,
            resume_after_product_id=None if completed else last_done,
            message=message,
            **base,
        )
