"""Store info returned to the dashboard. Data comes live from Tiendanube (never persisted);
only the name/language cached on the connection are used as fallback when it is unreachable.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from src.services.tiendanube.models import TNStore, localize

# active: live data from Tiendanube | unavailable: Tiendanube did not answer (cached data only)
StoreStatus = Literal["active", "unavailable"]


class StoreInfo(BaseModel):
    connection_id: uuid.UUID
    store_id: int
    status: StoreStatus
    name: str | None
    url: str | None
    domain: str | None
    email: str | None
    logo_url: str | None
    country: str | None
    language: str | None
    currency: str | None
    plan: str | None
    scopes: list[str]
    connected_at: datetime


def build_store_info(
    *,
    connection_id: uuid.UUID,
    store_id: int,
    store: TNStore | None,
    scopes: list[str],
    connected_at: datetime,
    fallback_name: str | None = None,
    fallback_language: str | None = None,
) -> StoreInfo:
    language = (store.main_language if store else None) or fallback_language
    return StoreInfo(
        connection_id=connection_id,
        store_id=store_id,
        status="active" if store else "unavailable",
        name=(localize(store.name, language) if store else None) or fallback_name,
        url=store.url_with_protocol if store else None,
        domain=store.original_domain if store else None,
        email=store.email if store else None,
        logo_url=_absolute_url(store.logo) if store else None,
        country=store.country if store else None,
        language=language,
        currency=store.main_currency if store else None,
        plan=store.plan_name if store else None,
        scopes=scopes,
        connected_at=connected_at,
    )


def split_scopes(scopes: str) -> list[str]:
    """`connections.scopes` is stored as a comma-separated, sorted string."""
    return [scope for scope in scopes.split(",") if scope]


def _absolute_url(url: str | None) -> str | None:
    """Tiendanube returns the logo as a protocol-relative URL (//dcdn-us.mitiendanube.com/...)."""
    if not url:
        return None
    return f"https:{url}" if url.startswith("//") else url
