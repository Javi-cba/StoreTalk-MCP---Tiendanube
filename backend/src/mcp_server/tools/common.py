"""Helpers shared by every tool module (text normalization, i18n payloads, money)."""

import re
import unicodedata
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from src.services.tiendanube.models import LocalizedText

DEFAULT_LANGUAGE = "es"

Rounding = Literal["none", "integer", "tens", "hundreds"]

_ROUNDING_STEP: dict[Rounding, Decimal] = {
    "none": Decimal("0.01"),
    "integer": Decimal("1"),
    "tens": Decimal("10"),
    "hundreds": Decimal("100"),
}


def i18n(text: str, language: str | None) -> LocalizedText:
    """Tiendanube i18n fields are written as {"<lang>": text} in the store main language."""
    return {language or DEFAULT_LANGUAGE: text}


def normalize(text: str) -> str:
    """Case/accent/space-insensitive key for matching user input against store data."""
    decomposed = unicodedata.normalize("NFKD", text)
    no_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", no_accents).strip().casefold()


def round_price(value: Decimal, rounding: Rounding) -> Decimal:
    step = _ROUNDING_STEP[rounding]
    rounded = (value / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * step
    return rounded.quantize(Decimal("0.01"))


def apply_percentage(value: Decimal, percentage: Decimal, rounding: Rounding) -> Decimal:
    return round_price(value * (Decimal(100) + percentage) / Decimal(100), rounding)
