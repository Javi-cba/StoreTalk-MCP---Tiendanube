"""Resolve category names, paths ("Hombre > Remeras") or ids. Reused by products,
coupons and pricing.
"""

import difflib
from functools import partial

from fastmcp.exceptions import ToolError

from src.mcp_server import context
from src.mcp_server.context import StoreContext
from src.mcp_server.tools.common import i18n, normalize
from src.services.tiendanube.models import TNCategory, localize

CategoryRef = int | str

_PATH_SEPARATOR = ">"


class CategoryIndex:
    """In-memory view of the store categories (max 1000, fetched once per tool call)."""

    def __init__(self, categories: list[TNCategory], language: str | None) -> None:
        self.language = language
        self.by_id = {c.id: c for c in categories}

    def name(self, category: TNCategory) -> str:
        return localize(category.name, self.language) or f"#{category.id}"

    def path(self, category: TNCategory) -> str:
        names = [self.name(category)]
        parent_id = category.parent
        seen = {category.id}
        while parent_id and parent_id in self.by_id and parent_id not in seen:
            seen.add(parent_id)
            parent = self.by_id[parent_id]
            names.append(self.name(parent))
            parent_id = parent.parent
        return f" {_PATH_SEPARATOR} ".join(reversed(names))

    def descendants(self, category_id: int) -> list[int]:
        children: dict[int, list[int]] = {}
        for c in self.by_id.values():
            if c.parent:
                children.setdefault(c.parent, []).append(c.id)
        result: list[int] = []
        stack = list(children.get(category_id, []))
        while stack:
            current = stack.pop()
            if current in result:
                continue
            result.append(current)
            stack.extend(children.get(current, []))
        return result

    def find(self, ref: CategoryRef) -> TNCategory | None:
        """Resolve an id, a name ("Remeras") or a path ("Hombre > Remeras").

        Raises ToolError when a name is ambiguous (same name under different parents).
        """
        if isinstance(ref, int) or ref.strip().isdigit():
            return self.by_id.get(int(ref))
        wanted = normalize(ref)
        if _PATH_SEPARATOR in ref:
            matches = [c for c in self.by_id.values() if normalize(self.path(c)) == wanted]
        else:
            matches = [c for c in self.by_id.values() if normalize(self.name(c)) == wanted]
        if not matches:
            # Tolerate singular/plural ("remera" -> "Remeras").
            matches = [
                c
                for c in self.by_id.values()
                if normalize(self.name(c)).rstrip("s") == wanted.rstrip("s")
            ]
        if len(matches) > 1:
            options = "; ".join(f"{self.path(c)} (id {c.id})" for c in matches)
            raise ToolError(
                f"Hay varias categorías llamadas '{ref}': {options}. "
                "Indicá cuál usando la ruta completa o el id."
            )
        return matches[0] if matches else None

    def require(self, ref: CategoryRef) -> TNCategory:
        found = self.find(ref)
        if found is not None:
            return found
        names = [self.path(c) for c in self.by_id.values()]
        suggestions = difflib.get_close_matches(str(ref), names, n=3, cutoff=0.5)
        hint = f" ¿Quisiste decir: {', '.join(suggestions)}?" if suggestions else ""
        raise ToolError(f"No existe la categoría '{ref}'.{hint}")


async def load_category_index(ctx: StoreContext) -> CategoryIndex:
    categories = await context.run_tiendanube(ctx, ctx.client.categories.list_all)
    return CategoryIndex(categories, ctx.language)


async def resolve_category_ids(
    ctx: StoreContext, refs: list[CategoryRef], *, create_missing: bool = False
) -> list[int]:
    """Map names/paths/ids to category ids. Optionally create the missing ones (top level)."""
    if not refs:
        return []
    index = await load_category_index(ctx)
    ids: list[int] = []
    for ref in refs:
        found = index.find(ref)
        if found is None and create_missing and isinstance(ref, str) and not ref.isdigit():
            name = ref.split(_PATH_SEPARATOR)[-1].strip()
            created = await context.run_tiendanube(
                ctx,
                partial(ctx.client.categories.create, {"name": i18n(name, ctx.language)}),
            )
            found = created
            index.by_id[found.id] = found
        elif found is None:
            index.require(ref)  # raises with suggestions
        assert found is not None
        if found.id not in ids:
            ids.append(found.id)
    return ids
