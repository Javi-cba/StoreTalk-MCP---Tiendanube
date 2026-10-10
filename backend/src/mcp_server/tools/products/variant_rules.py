"""Pure rules that let the variant tools infer what the user did not say.

"Add size L to the blue t-shirt" means: match "talle" with the product attribute
"Talle", write "L" like the existing sizes, create one L per existing color, and copy
price/weight/image from the sibling variant of the same color.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal

from src.mcp_server.tools.common import normalize
from src.services.tiendanube.models import TNVariant

_SYNONYMS: tuple[frozenset[str], ...] = (
    frozenset({"talle", "talla", "talles", "tallas", "size", "tamano", "tamanho", "medida"}),
    frozenset({"color", "colores", "colour", "cor", "cores"}),
    frozenset({"material", "tela", "tecido"}),
    frozenset({"modelo", "model", "estilo", "style"}),
    frozenset({"sabor", "flavor", "flavour"}),
)
_SIZE_ATTRIBUTES = _SYNONYMS[0]
_LETTER_SIZE = re.compile(r"^(x{0,4}s|m|x{0,4}l|\d?x{1,4}l|\d?xs|u|unico)$", re.IGNORECASE)
_SKU_SPLIT = re.compile(r"([-_/. ])")


def same_attribute(a: str, b: str) -> bool:
    na, nb = normalize(a), normalize(b)
    if na == nb:
        return True
    return any(na in group and nb in group for group in _SYNONYMS)


def match_attribute(name: str, attributes: Sequence[str]) -> int | None:
    for index, attribute in enumerate(attributes):
        if same_attribute(name, attribute):
            return index
    return None


def is_size_attribute(name: str) -> bool:
    return normalize(name) in _SIZE_ATTRIBUTES


def normalize_value(attribute: str, value: str, existing: Sequence[str]) -> str:
    """Write the value the way the store already writes it."""
    clean = re.sub(r"\s+", " ", value).strip()
    for current in existing:
        if normalize(current) == normalize(clean):
            return current
    if is_size_attribute(attribute) and _LETTER_SIZE.match(clean):
        return clean.upper()
    if existing and all(e[:1].isupper() for e in existing if e) and clean[:1].islower():
        return clean[:1].upper() + clean[1:]
    return clean


def derive_sku(
    template_sku: str | None, template_values: Sequence[str], new_values: Sequence[str]
) -> str | None:
    """REM-AZ-S + (Azul, S) -> (Azul, L) = REM-AZ-L. None when it can't be inferred safely."""
    if not template_sku:
        return None
    tokens = _SKU_SPLIT.split(template_sku)
    changed = False
    for old, new in zip(template_values, new_values, strict=False):
        if normalize(old) == normalize(new):
            continue
        hits = [i for i, t in enumerate(tokens) if t and normalize(t) == normalize(old)]
        if len(hits) != 1:
            return None
        tokens[hits[0]] = re.sub(r"\s+", "", new).upper() if tokens[hits[0]].isupper() else new
        changed = True
    return "".join(tokens) if changed else None


@dataclass
class PlannedVariant:
    values: list[str]
    template: TNVariant | None
    template_values: list[str] = field(default_factory=list)


def plan_combinations(
    fixed: dict[int, str],
    attribute_count: int,
    existing: Sequence[tuple[TNVariant, list[str]]],
) -> tuple[list[PlannedVariant], list[list[str]]]:
    """Expand a partial spec to full value combinations.

    Attributes the user did not mention take every combination that already exists in the
    product (adding size L to a product with colors Red/Blue creates Red/L and Blue/L).
    Returns (to_create, already_existing).
    """
    free = [i for i in range(attribute_count) if i not in fixed]
    if free:
        seen: list[tuple[str, ...]] = []
        for _, values in existing:
            key = tuple(values[i] if i < len(values) else "" for i in free)
            if all(key) and key not in seen:
                seen.append(key)
        combos = []
        for key in seen or [tuple("" for _ in free)]:
            values = ["" for _ in range(attribute_count)]
            for i, v in fixed.items():
                values[i] = v
            for i, v in zip(free, key, strict=True):
                values[i] = v
            combos.append(values)
    else:
        combos = [[fixed[i] for i in range(attribute_count)]]

    existing_keys = {tuple(normalize(v) for v in values) for _, values in existing}
    to_create: list[PlannedVariant] = []
    duplicates: list[list[str]] = []
    for values in combos:
        if tuple(normalize(v) for v in values) in existing_keys:
            duplicates.append(values)
            continue
        template, template_values = _best_template(values, free, existing)
        to_create.append(PlannedVariant(values, template, template_values))
    return to_create, duplicates


def _best_template(
    values: list[str], free: list[int], existing: Sequence[tuple[TNVariant, list[str]]]
) -> tuple[TNVariant | None, list[str]]:
    """Sibling sharing the most values (prefer the same color when adding a size)."""
    best: tuple[int, TNVariant | None, list[str]] = (-1, None, [])
    for variant, current in existing:
        score = sum(
            2 if i in free else 1
            for i, v in enumerate(values)
            if i < len(current) and normalize(current[i]) == normalize(v)
        )
        if score > best[0]:
            best = (score, variant, current)
    return best[1], best[2]


def inherited_fields(template: TNVariant | None) -> dict[str, object]:
    """Fields a new variant copies from its sibling unless the user overrides them."""
    if template is None:
        return {}
    data: dict[str, object] = {}
    for name in ("price", "promotional_price", "weight", "width", "height", "depth", "cost"):
        value = getattr(template, name)
        if value is not None:
            data[name] = str(value) if isinstance(value, Decimal) else value
    return data
