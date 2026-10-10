"""Coupons — https://tiendanube.github.io/api-documentation/resources/coupon

`code` is unique and alphanumeric. `type`: percentage | absolute | shipping.
`categories` and `products` are mutually exclusive.
"""

from typing import Any

from src.services.tiendanube.models import TNCoupon, TNPage
from src.services.tiendanube.resources._base import Resource
from src.services.tiendanube.scopes import Scope


class CouponsResource(Resource):
    async def list(self, params: dict[str, Any]) -> TNPage:
        """GET /coupons. Filters: q (code), valid, status, discount_type, sort_by, dates."""
        return await self._client.get_page("/coupons", scope=Scope.READ_COUPONS, params=params)

    async def get(self, coupon_id: int) -> TNCoupon:
        """GET /coupons/{id}"""
        data = await self._client.get_json(f"/coupons/{coupon_id}", scope=Scope.READ_COUPONS)
        return TNCoupon.model_validate(data)

    async def create(self, payload: dict[str, Any]) -> TNCoupon:
        """POST /coupons"""
        data = await self._client.send("POST", "/coupons", scope=Scope.WRITE_COUPONS, json=payload)
        return TNCoupon.model_validate(data)

    async def update(self, coupon_id: int, payload: dict[str, Any]) -> TNCoupon:
        """PUT /coupons/{id}"""
        data = await self._client.send(
            "PUT", f"/coupons/{coupon_id}", scope=Scope.WRITE_COUPONS, json=payload
        )
        return TNCoupon.model_validate(data)

    async def delete(self, coupon_id: int) -> None:
        """DELETE /coupons/{id} -> 200 {}"""
        await self._client.send("DELETE", f"/coupons/{coupon_id}", scope=Scope.WRITE_COUPONS)
