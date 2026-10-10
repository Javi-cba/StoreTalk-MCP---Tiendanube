"""Product variants — https://tiendanube.github.io/api-documentation/resources/product-variant

`values` must have one entry per product attribute (same order as `product.attributes`).
`stock_management` is read-only: send `"stock": ""` (or null) for unlimited stock.
"""

from typing import Any

from src.services.tiendanube.models import TNVariant
from src.services.tiendanube.resources._base import Resource
from src.services.tiendanube.scopes import Scope


class VariantsResource(Resource):
    async def all(self, product_id: int) -> list[TNVariant]:
        """GET /products/{id}/variants"""
        data = await self._client.get_json(
            f"/products/{product_id}/variants",
            scope=Scope.READ_PRODUCTS,
            params={"per_page": 200},
        )
        return [TNVariant.model_validate(v) for v in data]

    async def create(self, product_id: int, payload: dict[str, Any]) -> TNVariant:
        """POST /products/{id}/variants. Repeated values -> 422 "Variants cannot be repeated"."""
        data = await self._client.send(
            "POST", f"/products/{product_id}/variants", scope=Scope.WRITE_PRODUCTS, json=payload
        )
        return TNVariant.model_validate(data)

    async def update(self, product_id: int, variant_id: int, payload: dict[str, Any]) -> TNVariant:
        """PUT /products/{id}/variants/{variant_id}"""
        data = await self._client.send(
            "PUT",
            f"/products/{product_id}/variants/{variant_id}",
            scope=Scope.WRITE_PRODUCTS,
            json=payload,
        )
        return TNVariant.model_validate(data)

    async def patch_many(self, product_id: int, items: list[dict[str, Any]]) -> list[TNVariant]:
        """PATCH /products/{id}/variants — updates existing variants only (each item needs
        `id`), in a single request. Duplicated ids -> 422.
        """
        data = await self._client.send(
            "PATCH", f"/products/{product_id}/variants", scope=Scope.WRITE_PRODUCTS, json=items
        )
        return [TNVariant.model_validate(v) for v in data] if isinstance(data, list) else []

    async def delete(self, product_id: int, variant_id: int) -> None:
        """DELETE /products/{id}/variants/{variant_id} -> 200 {}"""
        await self._client.send(
            "DELETE", f"/products/{product_id}/variants/{variant_id}", scope=Scope.WRITE_PRODUCTS
        )
