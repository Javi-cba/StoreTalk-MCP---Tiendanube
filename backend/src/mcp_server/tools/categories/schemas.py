"""Output models of the category tools."""

from pydantic import BaseModel, Field

from src.mcp_server.tools.categories.resolver import CategoryIndex
from src.services.tiendanube.models import TNCategory


class CategorySummary(BaseModel):
    id: int
    name: str
    path: str = Field(description="Full path, e.g. 'Hombre > Remeras'.")
    parent_id: int | None
    subcategories_count: int
    visibility: str | None


class CategoryListResult(BaseModel):
    categories: list[CategorySummary]
    total: int


class CategoryDeleted(BaseModel):
    id: int
    name: str
    deleted: bool


def summarize(index: CategoryIndex, category: TNCategory) -> CategorySummary:
    return CategorySummary(
        id=category.id,
        name=index.name(category),
        path=index.path(category),
        parent_id=category.parent or None,
        subcategories_count=len(category.subcategories),
        visibility=category.visibility,
    )
