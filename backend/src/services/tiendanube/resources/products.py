"""Products — https://tiendanube.github.io/api-documentation/resources/product

Price, stock and dimensions live in the variants (a product created without variants
has one "virtual" variant): update them through `VariantsResource`.
"""

from typing import Any

from src.services.tiendanube.errors import TiendanubeNotFoundError
from src.services.tiendanube.models import TNPage, TNProduct
from src.services.tiendanube.resources._base import Resource
from src.services.tiendanube.scopes import Scope

MAX_IMAGES_ON_CREATE = 9  # Docs: add more with POST /products/{id}/images.
MAX_ATTRIBUTES = 3
MAX_VARIANTS = 1000


class ProductsResource(Resource):
    async def list(self, params: dict[str, Any]) -> TNPage:
        """GET /products. Filters: q, ids, category_id, published, min/max_stock,
        has_promotional_price, free_shipping, created/updated_at_min/max, sort_by,
        page, per_page (max 200), fields. Nothing is filtered in Python.
        """
        return await self._client.get_page("/products", scope=Scope.READ_PRODUCTS, params=params)

    async def get(self, product_id: int, fields: str | None = None) -> TNProduct:
        """GET /products/{id}"""
        data = await self._client.get_json(
            f"/products/{product_id}", scope=Scope.READ_PRODUCTS, params={"fields": fields}
        )
        return TNProduct.model_validate(data)

    async def get_by_sku(self, sku: str) -> TNProduct | None:
        """GET /products/sku/{sku} — first product with a variant that has this SKU."""
        try:
            data = await self._client.get_json(f"/products/sku/{sku}", scope=Scope.READ_PRODUCTS)
        except TiendanubeNotFoundError:
            return None
        return TNProduct.model_validate(data)

    async def create(self, payload: dict[str, Any]) -> TNProduct:
        """POST /products. Accepts `variants` and `images` (`src` only, max 9) inline."""
        data = await self._client.send(
            "POST", "/products", scope=Scope.WRITE_PRODUCTS, json=payload
        )
        return TNProduct.model_validate(data)

    async def update(self, product_id: int, payload: dict[str, Any]) -> TNProduct:
        """PUT /products/{id}. `categories: []` removes all; omit the key to keep them.
        Send `published` OR `visibility`, never both (422).
        """
        data = await self._client.send(
            "PUT", f"/products/{product_id}", scope=Scope.WRITE_PRODUCTS, json=payload
        )
        return TNProduct.model_validate(data)

    async def delete(self, product_id: int) -> None:
        """DELETE /products/{id} -> 200 {}"""
        await self._client.send("DELETE", f"/products/{product_id}", scope=Scope.WRITE_PRODUCTS)
