"""Coupon business rules checked before calling Tiendanube."""

import re
from datetime import date
from decimal import Decimal
from typing import Literal

from fastmcp.exceptions import ToolError

CouponType = Literal["percentage", "absolute", "shipping"]
CouponStatus = Literal["activated", "deactivated"]

CODE_ALLOWED = re.compile(r"^[A-Z0-9]+$")


def normalize_code(code: str) -> str:
    """Tiendanube codes are alphanumeric: 'verano 20' -> 'VERANO20'."""
    clean = re.sub(r"[\s\-_]+", "", code).upper()
    if not CODE_ALLOWED.match(clean):
        raise ToolError(
            f"El código '{code}' no es válido: solo letras y números, sin espacios ni símbolos."
        )
    return clean


def check_rules(
    type_: str | None,
    value: Decimal | None,
    start_date: date | None,
    end_date: date | None,
    has_categories: bool,
    has_products: bool,
) -> None:
    if type_ in ("percentage", "absolute") and value is None:
        raise ToolError("Indicá el valor del descuento (value).")
    if type_ == "percentage" and value is not None and not (0 < value <= 100):
        raise ToolError("El porcentaje tiene que estar entre 0 y 100.")
    if start_date and end_date and end_date < start_date:
        raise ToolError("La fecha de fin no puede ser anterior a la de inicio.")
    if has_categories and has_products:
        raise ToolError(
            "Un cupón puede limitarse a categorías o a productos, pero no a ambos a la vez."
        )
