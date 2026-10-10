"""Categories — https://tiendanube.github.io/api-documentation/resources/category

`subcategories` is read-only: re-parent a category by setting `parent` on the child.
Max 1000 categories per store, so `list_all` fits in 5 pages of 200.
"""

import builtins
from typing import Any

from src.services.tiendanube.models import TNCategory, TNPage
from src.services.tiendanube.resources._base import Resource
from src.services.tiendanube.scopes import Scope

_FIELDS = "id,name,description,handle,parent,subcategories,visibility"
_MAX_PAGES = 5


class CategoriesResource(Resource):
    async def list(self, params: dict[str, Any]) -> TNPage:
        """GET /categories. Filters: parent_id, handle (+language), created/updated_at_*."""
        return await self._client.get_page(
            "/categories", scope=Scope.READ_PRODUCTS, params={"fields": _FIELDS, **params}
        )

    async def list_all(self) -> builtins.list[TNCategory]:
        """Every category of the store (bounded by Tiendanube's 1000 limit)."""
        categories: builtins.list[TNCategory] = []
        for page in range(1, _MAX_PAGES + 1):
            result = await self.list({"page": page, "per_page": 200})
            categories.extend(TNCategory.model_validate(c) for c in result.items)
            if not result.has_more:
                break
        return categories

    async def create(self, payload: dict[str, Any]) -> TNCategory:
        """POST /categories (`name` required)."""
        data = await self._client.send(
            "POST", "/categories", scope=Scope.WRITE_PRODUCTS, json=payload
        )
        return TNCategory.model_validate(data)

    async def update(self, category_id: int, payload: dict[str, Any]) -> TNCategory:
        """PUT /categories/{id}"""
        data = await self._client.send(
            "PUT", f"/categories/{category_id}", scope=Scope.WRITE_PRODUCTS, json=payload
        )
        return TNCategory.model_validate(data)

    async def delete(self, category_id: int) -> None:
        """DELETE /categories/{id} -> 200 {}"""
        await self._client.send("DELETE", f"/categories/{category_id}", scope=Scope.WRITE_PRODUCTS)
