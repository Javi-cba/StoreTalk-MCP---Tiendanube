"""Tiendanube app installation, started by a user logged in with Clerk.

Docs: https://tiendanube.github.io/api-documentation/authentication

  GET  /api/tiendanube/install-url -> authorize URL with a `state` signed for this Clerk user
  POST /api/tiendanube/connect     -> exchanges the `code` received by the frontend at
                                      /connect/callback and stores the connection + scopes
The Partners panel "Redirect URL" must point to {FRONTEND_ORIGIN}/connect/callback.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentSession
from src.core.errors import ApiError
from src.core.oauth_state import create_state, verify_state
from src.database import get_db
from src.db import repositories
from src.services.tiendanube.client import TiendanubeClient, get_http_client
from src.services.tiendanube.errors import TiendanubeError
from src.services.tiendanube.models import TNStore, localize
from src.services.tiendanube.oauth import build_authorize_url, exchange_code, parse_scopes

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tiendanube", tags=["tiendanube"])


class InstallUrlResponse(BaseModel):
    url: str


class ConnectRequest(BaseModel):
    code: str = Field(min_length=1, max_length=512)
    # Installs started from the Tiendanube app store arrive without our state.
    state: str | None = Field(default=None, max_length=1024)


class ConnectedStoreResponse(BaseModel):
    connection_id: uuid.UUID
    store_id: int
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


@router.get("/install-url", response_model=InstallUrlResponse)
async def install_url(session: CurrentSession) -> InstallUrlResponse:
    return InstallUrlResponse(url=build_authorize_url(create_state(session.user_id)))


@router.post("/connect", response_model=ConnectedStoreResponse)
async def connect(
    body: ConnectRequest, session: CurrentSession, db: Annotated[AsyncSession, Depends(get_db)]
) -> ConnectedStoreResponse:
    if body.state is not None and not verify_state(body.state, session.user_id):
        raise ApiError(
            status.HTTP_400_BAD_REQUEST,
            "invalid_state",
            "El enlace de conexión venció o fue iniciado con otra cuenta. "
            "Volvé a conectar tu tienda desde StoreTalk.",
        )

    # Tiendanube calls first; the DB session is only used afterwards (short sessions).
    http = get_http_client()
    try:
        token = await exchange_code(http, body.code)
    except TiendanubeError as exc:
        raise ApiError(status.HTTP_400_BAD_REQUEST, "authorization_failed", exc.message) from exc

    store: TNStore | None = None
    try:
        store = await TiendanubeClient(http, token.store_id, token.access_token).get_store()
    except TiendanubeError:
        # The code is single-use: keep the connection even if the store info is unavailable.
        logger.warning("store info unavailable after install", extra={"store_id": token.store_id})

    scopes = parse_scopes(token.scope)
    language = store.main_language if store else None
    store_name = localize(store.name, language) if store else None

    user = await repositories.get_or_create_user(db, session.user_id)
    connection = await repositories.upsert_tiendanube_connection(
        db,
        user_id=user.id,
        store_id=token.store_id,
        access_token=token.access_token,
        scopes=",".join(scopes),
        store_name=store_name,
        store_language=language,
    )
    await db.commit()
    logger.info(
        "store connected",
        extra={
            "store_id": token.store_id,
            "user_id": str(user.id),
            "connection_id": str(connection.id),
        },
    )

    return ConnectedStoreResponse(
        connection_id=connection.id,
        store_id=token.store_id,
        name=store_name,
        url=store.url_with_protocol if store else None,
        domain=store.original_domain if store else None,
        email=store.email if store else None,
        logo_url=_absolute_url(store.logo) if store else None,
        country=store.country if store else None,
        language=language,
        currency=store.main_currency if store else None,
        plan=store.plan_name if store else None,
        scopes=scopes,
        connected_at=datetime.now(UTC),
    )


def _absolute_url(url: str | None) -> str | None:
    """Tiendanube returns the logo as a protocol-relative URL (//dcdn-us.mitiendanube.com/...)."""
    if not url:
        return None
    return f"https:{url}" if url.startswith("//") else url
