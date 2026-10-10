"""Stores connected by the logged-in user, for the dashboard ("Mis tiendas").

Paginated (`page` / `per_page`, 3 per page by default): only the stores of the requested page are
fetched live from Tiendanube (GET /store, one per connection, in parallel and with a short timeout).
A store that answers 401 (invalid token) is revoked, as everywhere else.
Docs: https://tiendanube.github.io/api-documentation/resources/store
"""

import asyncio
import logging
import math
import uuid
from typing import Annotated, Literal

import httpx
from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUser
from src.core import crypto
from src.core.errors import ApiError
from src.database import get_db
from src.db import repositories
from src.db.models import Connection
from src.mcp_server.auth import invalidate_cache
from src.schemas.stores import StoreInfo, build_store_info, split_scopes
from src.services.tiendanube.client import TiendanubeClient, get_http_client
from src.services.tiendanube.errors import TiendanubeAuthError, TiendanubeError
from src.services.tiendanube.models import TNStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stores", tags=["stores"])

# The list must stay snappy: a slow store is shown with its cached name instead of blocking.
LIVE_INFO_TIMEOUT_SECONDS = 8.0
# Each store costs a live Tiendanube request, so pages are small.
DEFAULT_PER_PAGE = 3
MAX_PER_PAGE = 12

LiveResult = tuple[Literal["active", "unavailable", "disconnected"], TNStore | None]


class StoresResponse(BaseModel):
    stores: list[StoreInfo]
    page: int
    per_page: int
    total: int
    total_pages: int


async def _fetch_live(http: httpx.AsyncClient, connection: Connection) -> LiveResult:
    token = crypto.decrypt(connection.access_token_encrypted, connection.key_version)
    client = TiendanubeClient(http, connection.store_id, token, split_scopes(connection.scopes))
    try:
        async with asyncio.timeout(LIVE_INFO_TIMEOUT_SECONDS):
            return "active", await client.get_store()
    except TiendanubeAuthError:
        return "disconnected", None
    except (TiendanubeError, TimeoutError):
        logger.warning("store info unavailable", extra={"store_id": connection.store_id})
        return "unavailable", None


@router.get("", response_model=StoresResponse)
async def list_stores(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    per_page: Annotated[int, Query(ge=1, le=MAX_PER_PAGE)] = DEFAULT_PER_PAGE,
) -> StoresResponse:
    connections, total = await repositories.list_active_connections(
        db, user.id, limit=per_page, offset=(page - 1) * per_page
    )
    # Ends the transaction so no DB connection is held while waiting on Tiendanube.
    await db.commit()

    http = get_http_client()
    results = await asyncio.gather(*(_fetch_live(http, c) for c in connections))

    disconnected = [
        c for c, (state, _) in zip(connections, results, strict=True) if state == "disconnected"
    ]
    if disconnected:
        for connection in disconnected:
            await repositories.revoke_connection(db, connection.id)
        await db.commit()
        invalidate_cache()
        logger.info("revoked stores with invalid token", extra={"user_id": str(user.id)})
        # The revoked ones no longer count; the next request already shifts the pages.
        total -= len(disconnected)

    return StoresResponse(
        page=page,
        per_page=per_page,
        total=total,
        total_pages=max(1, math.ceil(total / per_page)),
        stores=[
            build_store_info(
                connection_id=connection.id,
                store_id=connection.store_id,
                store=store,
                scopes=split_scopes(connection.scopes),
                connected_at=connection.created_at,
                fallback_name=connection.store_name,
                fallback_language=connection.store_language,
            )
            for connection, (state, store) in zip(connections, results, strict=True)
            if state != "disconnected"
        ],
    )


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_store(
    connection_id: uuid.UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Disconnect a store: deletes its Tiendanube credentials and revokes its MCP API keys.

    Tiendanube has no API to uninstall the app; the merchant can also remove it from their admin.
    """
    connection = await repositories.get_user_connection(db, user.id, connection_id)
    if connection is None:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "store_not_found",
            "No encontramos esa tienda entre tus tiendas conectadas.",
        )
    await repositories.revoke_connection(db, connection.id)
    await repositories.record_audit(
        db,
        user_id=user.id,
        connection_id=connection.id,
        tool_name="disconnect_store",
        entity_type="connection",
        entity_id=str(connection.id),
        before={"store_id": connection.store_id, "scopes": connection.scopes},
        after={"revoked": True, "credentials_deleted": True},
    )
    await db.commit()
    # API keys are cached ~60 s by the MCP verifier: drop the cache so they stop working now.
    invalidate_cache()
    logger.info(
        "store disconnected",
        extra={"user_id": str(user.id), "connection_id": str(connection.id)},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
