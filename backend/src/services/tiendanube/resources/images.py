"""Product images — https://tiendanube.github.io/api-documentation/resources/product-image

Source: `src` (public URL) or `attachment` (base64) + `filename`.
Formats: .gif, .jpg, .png, .webp. Max 10MB per image, 250 images per product.
`position` 1 = main image.
"""

from typing import Any

from src.services.tiendanube.models import TNImage
from src.services.tiendanube.resources._base import Resource
from src.services.tiendanube.scopes import Scope

ALLOWED_FORMATS = ("gif", "jpg", "png", "webp")
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGES_PER_PRODUCT = 250


class ImagesResource(Resource):
    async def all(self, product_id: int) -> list[TNImage]:
        """GET /products/{id}/images"""
        data = await self._client.get_json(
            f"/products/{product_id}/images", scope=Scope.READ_PRODUCTS, params={"per_page": 200}
        )
        return [TNImage.model_validate(i) for i in data]

    async def create(self, product_id: int, payload: dict[str, Any]) -> TNImage:
        """POST /products/{id}/images"""
        data = await self._client.send(
            "POST", f"/products/{product_id}/images", scope=Scope.WRITE_PRODUCTS, json=payload
        )
        return TNImage.model_validate(data)

    async def update(self, product_id: int, image_id: int, payload: dict[str, Any]) -> TNImage:
        """PUT /products/{id}/images/{image_id} (position, alt, src/attachment)."""
        data = await self._client.send(
            "PUT",
            f"/products/{product_id}/images/{image_id}",
            scope=Scope.WRITE_PRODUCTS,
            json=payload,
        )
        return TNImage.model_validate(data)

    async def delete(self, product_id: int, image_id: int) -> None:
        """DELETE /products/{id}/images/{image_id} -> 200 {}"""
        await self._client.send(
            "DELETE", f"/products/{product_id}/images/{image_id}", scope=Scope.WRITE_PRODUCTS
        )
