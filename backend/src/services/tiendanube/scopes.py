"""Tiendanube OAuth scopes required by each API call.

Docs: https://tiendanube.github.io/api-documentation/authentication
- `*_products` covers products, variants, images and categories.
- `*_coupons` covers coupons; `*_orders` covers orders.
- Any write scope implies the matching read scope.
"""

from collections.abc import Iterable
from enum import StrEnum


class Scope(StrEnum):
    READ_PRODUCTS = "read_products"
    WRITE_PRODUCTS = "write_products"
    READ_ORDERS = "read_orders"
    WRITE_ORDERS = "write_orders"
    READ_COUPONS = "read_coupons"
    WRITE_COUPONS = "write_coupons"
    READ_CUSTOMERS = "read_customers"


_DESCRIPTIONS: dict[str, str] = {
    Scope.READ_PRODUCTS: "Productos: ver productos, variantes, imágenes y categorías",
    Scope.WRITE_PRODUCTS: "Productos: crear, editar y eliminar productos, variantes, imágenes "
    "y categorías",
    Scope.READ_ORDERS: "Órdenes: ver órdenes",
    Scope.WRITE_ORDERS: "Órdenes: cerrar, reabrir, cancelar y editar órdenes",
    Scope.READ_COUPONS: "Cupones: ver cupones de descuento",
    Scope.WRITE_COUPONS: "Cupones: crear, editar y eliminar cupones de descuento",
    Scope.READ_CUSTOMERS: "Clientes: ver datos de clientes",
}


def parse_granted(raw: str | Iterable[str]) -> frozenset[str]:
    """`connections.scopes` is stored as "read_products,write_orders"."""
    items = raw.split(",") if isinstance(raw, str) else raw
    return frozenset(s.strip() for s in items if s.strip())


def is_granted(required: Scope, granted: frozenset[str]) -> bool:
    if required in granted:
        return True
    access, _, resource = required.value.partition("_")
    return access == "read" and f"write_{resource}" in granted


def missing_scope_message(scope: Scope) -> str:
    description = _DESCRIPTIONS.get(scope, scope.value)
    return (
        f"Falta el permiso de Tiendanube `{scope.value}` ({description}) para usar esta "
        "función. Pedile al dueño de la tienda que lo agregue desde el admin de StoreTalk, "
        "en los permisos de la tienda conectada, y volvé a intentar."
    )
