"""Product image tools: add (URL or base64), reorder/alt, delete."""

from functools import partial
from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from src.mcp_server import context
from src.mcp_server.tools.common import i18n, normalize
from src.mcp_server.tools.products.image_input import ImageInput, to_payload
from src.mcp_server.tools.products.schemas import ImageSummary, attribute_names, variant_values
from src.mcp_server.tools.products.variant_rules import match_attribute
from src.services.tiendanube.resources.images import MAX_IMAGES_PER_PRODUCT


class AddImagesResult(BaseModel):
    product_id: int
    uploaded: list[ImageSummary]
    failed: list[str]
    linked_variant_ids: list[int] = Field(
        description="Variants that now show the first uploaded image."
    )


class ImageDeleted(BaseModel):
    product_id: int
    image_id: int
    deleted: bool


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Add product images", openWorldHint=True))
    async def add_product_images(
        product_id: Annotated[int, Field(gt=0)],
        images: Annotated[
            list[ImageInput],
            Field(
                min_length=1,
                description="By public URL (preferred) or base64. JPG, PNG, GIF or WEBP, "
                "< 10MB each.",
            ),
        ],
        for_variants: Annotated[
            dict[str, str] | None,
            Field(
                description="Show the first image on the matching variants, e.g. "
                "{'Color': 'Rojo'} links it to every red variant."
            ),
        ] = None,
    ) -> AddImagesResult:
        """Upload images to an existing product. `position=1` makes it the main image.

        Each image is uploaded separately: if one fails (format, size, broken URL) the rest
        are still uploaded and the failure is reported.
        """
        ctx = await context.get_store_context()
        lang = ctx.language
        product = await context.run_tiendanube(ctx, lambda: ctx.client.products.get(product_id))
        if len(product.images) + len(images) > MAX_IMAGES_PER_PRODUCT:
            raise ToolError(
                f"Tiendanube permite hasta {MAX_IMAGES_PER_PRODUCT} imágenes por producto "
                f"(ya tiene {len(product.images)})."
            )
        targets: list[int] = []
        if for_variants:
            attributes = attribute_names(product, lang)
            wanted: dict[int, str] = {}
            for key, value in for_variants.items():
                index = match_attribute(key, attributes)
                if index is None:
                    raise ToolError(f"El producto no tiene el atributo '{key}'.")
                wanted[index] = normalize(value)
            targets = [
                v.id
                for v in product.variants
                if all(
                    i < len(vals) and normalize(vals[i]) == val
                    for i, val in wanted.items()
                    for vals in [variant_values(v, lang)]
                )
            ]
            if not targets:
                raise ToolError(f"Ninguna variante coincide con {for_variants}.")

        uploaded: list[ImageSummary] = []
        failed: list[str] = []
        for index, image in enumerate(images, start=1):
            try:
                payload = to_payload(image, lang)
                created = await context.run_tiendanube(
                    ctx, partial(ctx.client.images.create, product_id, payload)
                )
            except ToolError as exc:
                failed.append(f"Imagen {index} ({image.url or image.filename or 'base64'}): {exc}")
                continue
            uploaded.append(ImageSummary(id=created.id, src=created.src, position=created.position))

        linked: list[int] = []
        if uploaded and targets:
            image_id = uploaded[0].id
            items: list[dict[str, Any]] = [{"id": t, "image_id": image_id} for t in targets]
            await context.run_tiendanube(
                ctx, lambda: ctx.client.variants.patch_many(product_id, items)
            )
            linked = targets
        if uploaded:
            await context.record_audit(
                ctx,
                tool_name="add_product_images",
                entity_type="product",
                entity_id=product_id,
                before=None,
                after={
                    "images": [u.model_dump(mode="json") for u in uploaded],
                    "linked_variant_ids": linked,
                },
            )
        return AddImagesResult(
            product_id=product_id, uploaded=uploaded, failed=failed, linked_variant_ids=linked
        )

    @mcp.tool(annotations=ToolAnnotations(title="Update product image", openWorldHint=True))
    async def update_product_image(
        product_id: Annotated[int, Field(gt=0)],
        image_id: Annotated[int, Field(gt=0)],
        position: Annotated[int | None, Field(ge=1, description="1 = main image.")] = None,
        alt: Annotated[str | None, Field(max_length=255, description="Alt text (SEO).")] = None,
    ) -> ImageSummary:
        """Reorder an image (position 1 = main image) or change its alt text."""
        payload: dict[str, Any] = {}
        ctx = await context.get_store_context()
        if position is not None:
            payload["position"] = position
        if alt is not None:
            payload["alt"] = i18n(alt, ctx.language)
        if not payload:
            raise ToolError("Indicá position o alt.")
        updated = await context.run_tiendanube(
            ctx, lambda: ctx.client.images.update(product_id, image_id, payload)
        )
        await context.record_audit(
            ctx,
            tool_name="update_product_image",
            entity_type="image",
            entity_id=image_id,
            before=None,
            after=updated.model_dump(mode="json"),
        )
        return ImageSummary(id=updated.id, src=updated.src, position=updated.position)

    @mcp.tool(
        annotations=ToolAnnotations(
            title="Delete product image", destructiveHint=True, openWorldHint=True
        )
    )
    async def delete_product_image(
        product_id: Annotated[int, Field(gt=0)],
        image_id: Annotated[int, Field(gt=0, description="From get_product.images.")],
    ) -> ImageDeleted:
        """Delete one image of a product. Cannot be undone."""
        ctx = await context.get_store_context()
        await context.run_tiendanube(ctx, lambda: ctx.client.images.delete(product_id, image_id))
        await context.record_audit(
            ctx,
            tool_name="delete_product_image",
            entity_type="image",
            entity_id=image_id,
            before={"product_id": product_id},
            after=None,
        )
        return ImageDeleted(product_id=product_id, image_id=image_id, deleted=True)
