from decimal import Decimal

from src.mcp_server.tools.products.variant_rules import (
    derive_sku,
    match_attribute,
    normalize_value,
    plan_combinations,
)
from src.services.tiendanube.models import TNVariant


def test_attribute_synonyms() -> None:
    assert match_attribute("talla", ["Color", "Talle"]) == 1
    assert match_attribute("SIZE", ["Talle"]) == 0
    assert match_attribute("colour", ["Color"]) == 0
    assert match_attribute("Material", ["Color"]) is None


def test_values_follow_store_spelling() -> None:
    assert normalize_value("Talle", "l", ["S", "M"]) == "L"
    assert normalize_value("Talle", "xxl", []) == "XXL"
    assert normalize_value("Color", "rojo", ["Azul"]) == "Rojo"
    assert normalize_value("Color", "AZUL", ["Azul"]) == "Azul"


def test_derive_sku() -> None:
    assert derive_sku("REM-AZ-S", ["Azul", "S"], ["Azul", "L"]) == "REM-AZ-L"
    assert derive_sku("REM001", ["S"], ["L"]) is None
    assert derive_sku(None, ["S"], ["L"]) is None


def test_plan_expands_missing_attributes_and_skips_existing() -> None:
    red_s = TNVariant(id=1, price=Decimal("100"))
    blue_s = TNVariant(id=2, price=Decimal("120"))
    red_l = TNVariant(id=3, price=Decimal("100"))
    existing = [(red_s, ["Rojo", "S"]), (blue_s, ["Azul", "S"]), (red_l, ["Rojo", "L"])]

    to_create, duplicates = plan_combinations({1: "L"}, 2, existing)

    assert [p.values for p in to_create] == [["Azul", "L"]]
    assert to_create[0].template is blue_s  # same color sibling
    assert duplicates == [["Rojo", "L"]]
