"""Variant tools: add (with inference), update and delete product variants."""

from decimal import Decimal
from functools import partial
from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from src.mcp_server import context
from src.mcp_server.context import StoreContext
from src.mcp_server.tools.common import i18n, normalize
from src.mcp_server.tools.products.schemas import (
    VariantSummary,
    attribute_names,
    summarize_variant,
    variant_values,
)
from src.mcp_server.tools.products.variant_rules import (
    derive_sku,
    inherited_fields,
    match_attribute,
    normalize_value,
    plan_combinations,
)
from src.services.tiendanube.models import TNProduct, TNVariant, localize
from src.services.tiendanube.resources.products import MAX_ATTRIBUTES, MAX_VARIANTS

Price = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]


class VariantSpec(BaseModel):
    values: Annotated[
        dict[str, str],
        Field(
            description="Only what the user said, e.g. {'Talle': 'L'}. Attributes left out "
            "are expanded to every existing combination (one L per existing color)."
        ),
    ]
    price: Price | None = None
    promotional_price: Price | None = None
    stock: Annotated[
        int | None,
        Field(ge=0, description="Omit: 0 if siblings track stock, unlimited otherwise."),
    ] = None
    sku: Annotated[str | None, Field(description="Omit to derive it from a sibling SKU.")] = None


class AddVariantsResult(BaseModel):
    product_id: int
    product_name: str | None
    attributes: list[str]
    created: list[VariantSummary]
    skipped_existing: list[dict[str, str]] = Field(
        description="Combinations that already existed and were not created again."
    )
    failed: list[str]
    assumptions: list[str] = Field(description="What was inferred; tell it to the user.")


class VariantDeleted(BaseModel):
    product_id: int
    variant_id: int
    values: dict[str, str]
    deleted: bool


async def _load_product(ctx: StoreContext, product_id: int) -> TNProduct:
    return await context.run_tiendanube(ctx, lambda: ctx.client.products.get(product_id))


def _find_variant(
    product: TNProduct,
    attributes: list[str],
    language: str | None,
    variant_id: int | None,
    values: dict[str, str] | None,
    sku: str | None,
) -> TNVariant:
    if variant_id is not None:
        for variant in product.variants:
            if variant.id == variant_id:
                return variant
        raise ToolError(f"El producto {product.id} no tiene la variante {variant_id}.")
    if sku:
        matches = [v for v in product.variants if v.sku and normalize(v.sku) == normalize(sku)]
    elif values:
        wanted: dict[int, str] = {}
        for key, value in values.items():
            index = match_attribute(key, attributes)
            if index is None:
                raise ToolError(
                    f"El producto no tiene el atributo '{key}'. Atributos: "
                    f"{', '.join(attributes) or 'ninguno'}."
                )
            wanted[index] = normalize(value)
        matches = [
            v
            for v in product.variants
            if all(
                i < len(vals) and normalize(vals[i]) == val
                for i, val in wanted.items()
                for vals in [variant_values(v, language)]
            )
        ]
    elif len(product.variants) == 1:
        return product.variants[0]
    else:
        raise ToolError("Indicá la variante: variant_id, sku o sus valores (ej. {'Talle': 'M'}).")
    if not matches:
        raise ToolError("No encontré esa variante en el producto. Revisá con get_product.")
    if len(matches) > 1:
        options = "; ".join(
            f"{dict(zip(attributes, variant_values(v, language), strict=False))} (id {v.id})"
            for v in matches
        )
        raise ToolError(f"Hay varias variantes que coinciden: {options}. Indicá cuál.")
    return matches[0]


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Add product variants", openWorldHint=True))
    async def add_product_variants(
        product_id: Annotated[int, Field(gt=0)],
        variants: Annotated[
            list[VariantSpec],
            Field(min_length=1, description="One item per new value, e.g. talle L and XL."),
        ],
        existing_variant_values: Annotated[
            dict[str, str] | None,
            Field(
                description="Only when adding a NEW attribute (e.g. the product had no sizes): "
                "the value that the current variants take, e.g. {'Talle': 'M'}."
            ),
        ] = None,
    ) -> AddVariantsResult:
        """Add variants to a product, inferring everything the user didn't say.

        "Add size L to the t-shirt" -> variants=[{'values': {'Talle': 'L'}}]. The tool:
        - matches the attribute name with the product's (talle/talla/size, color/colour...)
          and writes the value like the existing ones ('l' -> 'L');
        - creates one variant per existing combination of the other attributes (an L for
          each color) and skips combinations that already exist;
        - copies price, promotional price, weight, dimensions, cost and image from the
          closest sibling (same color) and derives the SKU (REM-AZ-M -> REM-AZ-L);
        - stock: 0 if siblings track stock, unlimited otherwise, unless `stock` is given.
        Report `assumptions` back to the user.
        """
        ctx = await context.get_store_context()
        lang = ctx.language
        product = await _load_product(ctx, product_id)
        attributes = attribute_names(product, lang)
        existing = [(v, variant_values(v, lang)) for v in product.variants]
        assumptions: list[str] = []

        # 1. New attributes (keys that don't match any current attribute).
        new_attributes: list[str] = []
        for spec in variants:
            for key in spec.values:
                if (
                    match_attribute(key, attributes) is None
                    and match_attribute(key, new_attributes) is None
                ):
                    new_attributes.append(key.strip().capitalize())
        if len(attributes) + len(new_attributes) > MAX_ATTRIBUTES:
            raise ToolError(
                f"Tiendanube permite hasta {MAX_ATTRIBUTES} atributos por producto. El producto "
                f"ya tiene: {', '.join(attributes) or 'ninguno'}."
            )
        if new_attributes:
            current_values: list[str] = []
            for attribute in new_attributes:
                given = next(
                    (
                        v
                        for k, v in (existing_variant_values or {}).items()
                        if match_attribute(k, [attribute]) is not None
                    ),
                    None,
                )
                if not given:
                    raise ToolError(
                        f"El producto '{localize(product.name, lang)}' todavía no tiene "
                        f"'{attribute}'. Preguntale al usuario qué {attribute.lower()} tienen las "
                        f"variantes actuales ({len(product.variants)}) y pasalo en "
                        f"existing_variant_values, ej. {{'{attribute}': '...'}}."
                    )
                current_values.append(normalize_value(attribute, given, []))
            all_attributes = attributes + new_attributes
            await context.run_tiendanube(
                ctx,
                lambda: ctx.client.products.update(
                    product_id, {"attributes": [i18n(a, lang) for a in all_attributes]}
                ),
            )
            items = [
                {"id": v.id, "values": [i18n(x, lang) for x in values + current_values]}
                for v, values in existing
            ]
            await context.run_tiendanube(
                ctx, lambda: ctx.client.variants.patch_many(product_id, items)
            )
            existing = [(v, values + current_values) for v, values in existing]
            attributes = all_attributes
            assumptions.append(
                f"Se agregó el atributo {', '.join(new_attributes)}; las variantes existentes "
                f"quedaron como {', '.join(current_values)}."
            )

        # 2. Expand each spec into concrete combinations.
        plan: list[tuple[VariantSpec, list[str], TNVariant | None, list[str]]] = []
        skipped: list[dict[str, str]] = []
        for spec in variants:
            fixed: dict[int, str] = {}
            for key, value in spec.values.items():
                index = match_attribute(key, attributes)
                assert index is not None
                siblings = [vals[index] for _, vals in existing if index < len(vals)]
                fixed[index] = normalize_value(attributes[index], value, siblings)
                if normalize(key) != normalize(attributes[index]):
                    assumptions.append(
                        f"'{key}' se interpretó como el atributo '{attributes[index]}'."
                    )
            to_create, duplicates = plan_combinations(fixed, len(attributes), existing)
            skipped += [dict(zip(attributes, d, strict=True)) for d in duplicates]
            planned_keys = {tuple(normalize(x) for x in p[1]) for p in plan}
            for item in to_create:
                if tuple(normalize(x) for x in item.values) not in planned_keys:
                    plan.append((spec, item.values, item.template, item.template_values))
            missing = [attributes[i] for i in range(len(attributes)) if i not in fixed]
            if missing and len(to_create) > 1:
                assumptions.append(
                    f"Se creó una variante por cada {', '.join(missing).lower()} existente "
                    f"({len(to_create)} en total)."
                )
        if len(product.variants) + len(plan) > MAX_VARIANTS:
            raise ToolError(f"Tiendanube permite hasta {MAX_VARIANTS} variantes por producto.")

        # 3. Create them (POST is never retried; failures are reported one by one).
        created: list[VariantSummary] = []
        failed: list[str] = []
        for spec, values, template, template_values in plan:
            payload: dict[str, Any] = {
                **inherited_fields(template),
                "values": [i18n(v, lang) for v in values],
            }
            if spec.price is not None:
                payload["price"] = str(spec.price)
            if spec.promotional_price is not None:
                payload["promotional_price"] = str(spec.promotional_price)
            if spec.stock is not None:
                payload["stock"] = spec.stock
            else:
                payload["stock"] = "" if template is None or template.stock is None else 0
            sku = spec.sku if spec.sku and len(plan) == 1 else None
            sku = sku or derive_sku(template.sku if template else None, template_values, values)
            if sku:
                payload["sku"] = sku
            if template and template.image_id:
                payload["image_id"] = template.image_id
            label = dict(zip(attributes, values, strict=True))
            try:
                variant = await context.run_tiendanube(
                    ctx, partial(ctx.client.variants.create, product_id, payload)
                )
            except ToolError as exc:
                failed.append(f"{label}: {exc}")
                continue
            created.append(summarize_variant(variant, attributes, lang))
            if template is not None and spec.price is None:
                assumptions.append(
                    f"{label}: precio copiado de la variante "
                    f"{dict(zip(attributes, template_values, strict=False))}."
                )
            if spec.stock is None:
                stock_text = "ilimitado" if payload["stock"] == "" else "0"
                assumptions.append(f"{label}: stock {stock_text} (no se indicó cantidad).")

        if created:
            await context.record_audit(
                ctx,
                tool_name="add_product_variants",
                entity_type="product",
                entity_id=product_id,
                before={"variants": [v.model_dump(mode="json") for v in product.variants]},
                after={"created": [c.model_dump(mode="json") for c in created]},
            )
        return AddVariantsResult(
            product_id=product_id,
            product_name=localize(product.name, lang),
            attributes=attributes,
            created=created,
            skipped_existing=skipped,
            failed=failed,
            assumptions=assumptions,
        )

    @mcp.tool(annotations=ToolAnnotations(title="Update variant", openWorldHint=True))
    async def update_variant(
        product_id: Annotated[int, Field(gt=0)],
        variant_id: Annotated[int | None, Field(gt=0)] = None,
        values: Annotated[
            dict[str, str] | None,
            Field(description="Find the variant by its values, e.g. {'Talle': 'M'}."),
        ] = None,
        sku: Annotated[str | None, Field(description="Find the variant by SKU.")] = None,
        price: Price | None = None,
        promotional_price: Price | None = None,
        remove_promotional_price: bool = False,
        stock: Annotated[int | None, Field(ge=0)] = None,
        unlimited_stock: Annotated[bool, Field(description="Set unlimited stock.")] = False,
        new_sku: str | None = None,
        barcode: str | None = None,
        cost: Price | None = None,
        weight: Annotated[Decimal | None, Field(ge=0, description="kg")] = None,
        width: Annotated[Decimal | None, Field(ge=0, description="cm")] = None,
        height: Annotated[Decimal | None, Field(ge=0, description="cm")] = None,
        depth: Annotated[Decimal | None, Field(ge=0, description="cm")] = None,
        image_id: Annotated[
            int | None, Field(gt=0, description="Product image to show for this variant.")
        ] = None,
        new_values: Annotated[
            dict[str, str] | None,
            Field(description="Rename values, e.g. {'Color': 'Azul marino'}."),
        ] = None,
    ) -> VariantSummary:
        """Edit one variant (price, stock, SKU, cost, weight, image...). Find it by
        `variant_id`, `sku` or `values` ({'Talle': 'M', 'Color': 'Rojo'}). If the product has
        a single variant, no selector is needed.
        """
        ctx = await context.get_store_context()
        lang = ctx.language
        product = await _load_product(ctx, product_id)
        attributes = attribute_names(product, lang)
        variant = _find_variant(product, attributes, lang, variant_id, values, sku)

        payload: dict[str, Any] = {}
        for name, value in {
            "price": price,
            "promotional_price": promotional_price,
            "cost": cost,
            "weight": weight,
            "width": width,
            "height": height,
            "depth": depth,
        }.items():
            if value is not None:
                payload[name] = str(value)
        if remove_promotional_price:
            payload["promotional_price"] = None
        effective_price = price if price is not None else variant.price
        if (
            promotional_price is not None
            and effective_price is not None
            and promotional_price >= effective_price
        ):
            raise ToolError("El precio promocional tiene que ser menor al precio.")
        if unlimited_stock:
            payload["stock"] = ""
        elif stock is not None:
            payload["stock"] = stock
        if new_sku is not None:
            payload["sku"] = new_sku
        if barcode is not None:
            payload["barcode"] = barcode
        if image_id is not None:
            if image_id not in {i.id for i in product.images}:
                raise ToolError(f"La imagen {image_id} no pertenece al producto {product_id}.")
            payload["image_id"] = image_id
        if new_values:
            current = variant_values(variant, lang)
            for key, renamed in new_values.items():
                index = match_attribute(key, attributes)
                if index is None:
                    raise ToolError(f"El producto no tiene el atributo '{key}'.")
                current[index] = renamed.strip()
            payload["values"] = [i18n(v, lang) for v in current]
        if not payload:
            raise ToolError("No indicaste ningún cambio para la variante.")

        updated = await context.run_tiendanube(
            ctx, lambda: ctx.client.variants.update(product_id, variant.id, payload)
        )
        await context.record_audit(
            ctx,
            tool_name="update_variant",
            entity_type="variant",
            entity_id=variant.id,
            before=variant.model_dump(mode="json"),
            after=updated.model_dump(mode="json"),
        )
        return summarize_variant(updated, attributes, lang)

    @mcp.tool(
        annotations=ToolAnnotations(
            title="Delete variant", destructiveHint=True, openWorldHint=True
        )
    )
    async def delete_variant(
        product_id: Annotated[int, Field(gt=0)],
        variant_id: Annotated[int | None, Field(gt=0)] = None,
        values: Annotated[dict[str, str] | None, Field(description="e.g. {'Talle': 'XXL'}")] = None,
        sku: str | None = None,
    ) -> VariantDeleted:
        """Delete one variant of a product (e.g. size XXL). A product needs at least one
        variant: to remove the whole product use delete_product. Cannot be undone.
        """
        ctx = await context.get_store_context()
        lang = ctx.language
        product = await _load_product(ctx, product_id)
        attributes = attribute_names(product, lang)
        variant = _find_variant(product, attributes, lang, variant_id, values, sku)
        if len(product.variants) == 1:
            raise ToolError(
                "Es la única variante del producto. Para quitarlo de la tienda usá "
                "delete_product o update_product(published=false)."
            )
        await context.run_tiendanube(
            ctx, lambda: ctx.client.variants.delete(product_id, variant.id)
        )
        await context.record_audit(
            ctx,
            tool_name="delete_variant",
            entity_type="variant",
            entity_id=variant.id,
            before=variant.model_dump(mode="json"),
            after=None,
        )
        return VariantDeleted(
            product_id=product_id,
            variant_id=variant.id,
            values=dict(zip(attributes, variant_values(variant, lang), strict=False)),
            deleted=True,
        )
