"""Category tools: list, create, update, delete."""

from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from src.mcp_server import context
from src.mcp_server.tools.categories.resolver import CategoryRef, load_category_index
from src.mcp_server.tools.categories.schemas import (
    CategoryDeleted,
    CategoryListResult,
    CategorySummary,
    summarize,
)
from src.mcp_server.tools.common import i18n, normalize

Visibility = Literal["visible", "hidden"]


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(title="List categories", readOnlyHint=True, openWorldHint=True)
    )
    async def list_categories(
        q: Annotated[
            str | None, Field(description="Only categories whose name contains this text.")
        ] = None,
    ) -> CategoryListResult:
        """List the store categories with their full path ('Hombre > Remeras') and ids.

        Use it to find a category id before filtering products or creating coupons.
        Other tools also accept category names directly.
        """
        ctx = await context.get_store_context()
        index = await load_category_index(ctx)
        wanted = normalize(q) if q else None
        items = [
            summarize(index, c)
            for c in index.by_id.values()
            if wanted is None or wanted in normalize(index.path(c))
        ]
        items.sort(key=lambda s: normalize(s.path))
        return CategoryListResult(categories=items, total=len(items))

    @mcp.tool(annotations=ToolAnnotations(title="Create category", openWorldHint=True))
    async def create_category(
        name: Annotated[str, Field(min_length=1, max_length=255, description="Category name.")],
        parent: Annotated[
            CategoryRef | None,
            Field(description="Parent category (name, 'A > B' path or id) to nest it under."),
        ] = None,
        description: Annotated[str | None, Field(description="Category description.")] = None,
        visibility: Annotated[Visibility | None, Field(description="Default: visible.")] = None,
    ) -> CategorySummary:
        """Create a category, optionally as a subcategory of another one."""
        ctx = await context.get_store_context()
        index = await load_category_index(ctx)
        payload: dict[str, object] = {"name": i18n(name.strip(), ctx.language)}
        if parent is not None:
            payload["parent"] = index.require(parent).id
        if description is not None:
            payload["description"] = i18n(description, ctx.language)
        if visibility is not None:
            payload["visibility"] = visibility
        created = await context.run_tiendanube(ctx, lambda: ctx.client.categories.create(payload))
        index.by_id[created.id] = created
        await context.record_audit(
            ctx,
            tool_name="create_category",
            entity_type="category",
            entity_id=created.id,
            before=None,
            after=created.model_dump(mode="json"),
        )
        return summarize(index, created)

    @mcp.tool(annotations=ToolAnnotations(title="Update category", openWorldHint=True))
    async def update_category(
        category: Annotated[CategoryRef, Field(description="Category name, path or id.")],
        name: Annotated[str | None, Field(min_length=1, max_length=255)] = None,
        parent: Annotated[
            CategoryRef | None,
            Field(description="New parent (name/path/id). Use 0 to move it to the top level."),
        ] = None,
        description: Annotated[str | None, Field()] = None,
        visibility: Annotated[Visibility | None, Field()] = None,
    ) -> CategorySummary:
        """Rename a category, move it under another parent, or change description/visibility."""
        ctx = await context.get_store_context()
        index = await load_category_index(ctx)
        current = index.require(category)
        payload: dict[str, object] = {}
        if name is not None:
            payload["name"] = i18n(name.strip(), ctx.language)
        if parent is not None:
            if parent in (0, "0"):
                payload["parent"] = 0
            else:
                new_parent = index.require(parent)
                if new_parent.id == current.id or new_parent.id in index.descendants(current.id):
                    raise ToolError("Una categoría no puede ser hija de sí misma ni de sus hijas.")
                payload["parent"] = new_parent.id
        if description is not None:
            payload["description"] = i18n(description, ctx.language)
        if visibility is not None:
            payload["visibility"] = visibility
        if not payload:
            raise ToolError("No indicaste ningún cambio para la categoría.")
        updated = await context.run_tiendanube(
            ctx, lambda: ctx.client.categories.update(current.id, payload)
        )
        index.by_id[updated.id] = updated
        await context.record_audit(
            ctx,
            tool_name="update_category",
            entity_type="category",
            entity_id=current.id,
            before=current.model_dump(mode="json"),
            after=updated.model_dump(mode="json"),
        )
        return summarize(index, updated)

    @mcp.tool(
        annotations=ToolAnnotations(
            title="Delete category", destructiveHint=True, openWorldHint=True
        )
    )
    async def delete_category(
        category: Annotated[CategoryRef, Field(description="Category name, path or id.")],
    ) -> CategoryDeleted:
        """Delete a category. Products are kept (they just lose this category).

        Confirm with the user before calling it: it cannot be undone.
        """
        ctx = await context.get_store_context()
        index = await load_category_index(ctx)
        current = index.require(category)
        await context.run_tiendanube(ctx, lambda: ctx.client.categories.delete(current.id))
        await context.record_audit(
            ctx,
            tool_name="delete_category",
            entity_type="category",
            entity_id=current.id,
            before=current.model_dump(mode="json"),
            after=None,
        )
        return CategoryDeleted(id=current.id, name=index.path(current), deleted=True)
