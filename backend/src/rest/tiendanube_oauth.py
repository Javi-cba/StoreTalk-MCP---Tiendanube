"""Tiendanube app installation.

Docs: https://tiendanube.github.io/api-documentation/authentication

Until Clerk + the frontend exist, the backend handles the redirect itself:
  GET /api/tiendanube/install   -> 302 to Tiendanube's authorize page (signed `state`)
  GET /api/tiendanube/callback  -> exchanges `code`, stores the connection and returns a
                                   first MCP API key (development only; shown once).
The Partners panel "Redirect URL" must point to {PUBLIC_BASE_URL}/api/tiendanube/callback.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.core.oauth_state import create_state, verify_state
from src.database import get_db
from src.db import repositories
from src.services.tiendanube.client import TiendanubeClient, get_http_client
from src.services.tiendanube.errors import TiendanubeError
from src.services.tiendanube.models import localize
from src.services.tiendanube.oauth import build_authorize_url, exchange_code

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tiendanube", tags=["tiendanube"])

# Placeholder owner until Clerk is wired; replaced by the JWT user in POST /connect.
DEV_CLERK_USER_ID = "dev_local"


class InstallUrlResponse(BaseModel):
    url: str


class DevConnectResponse(BaseModel):
    connection_id: str
    store_id: int
    store_name: str | None
    scopes: str
    api_key: str
    api_key_note: str = "Shown only once. Use it as 'Authorization: Bearer <api_key>' on /mcp."


@router.get("/install-url", response_model=InstallUrlResponse)
async def install_url() -> InstallUrlResponse:
    return InstallUrlResponse(url=build_authorize_url(create_state()))


@router.get("/install", include_in_schema=False)
async def install() -> RedirectResponse:
    return RedirectResponse(build_authorize_url(create_state()))


@router.get("/callback", response_model=DevConnectResponse)
async def callback(
    code: str, db: Annotated[AsyncSession, Depends(get_db)], state: str | None = None
) -> DevConnectResponse:
    settings = get_settings()
    if not settings.is_development:
        # In production the frontend receives the code and calls POST /connect with a JWT.
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    # Installs started from the Tiendanube app store arrive without our state.
    if state is not None and not verify_state(state):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired state")

    http = get_http_client()
    try:
        token = await exchange_code(http, code)
        store = await TiendanubeClient(http, token.store_id, token.access_token).get_store()
    except TiendanubeError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, exc.message) from exc

    user = await repositories.get_or_create_user(db, DEV_CLERK_USER_ID)
    connection = await repositories.upsert_tiendanube_connection(
        db,
        user_id=user.id,
        store_id=token.store_id,
        access_token=token.access_token,
        scopes=token.scope,
        store_name=localize(store.name, store.main_language),
        store_language=store.main_language,
    )
    _, plaintext = await repositories.create_api_key(
        db, user_id=user.id, connection_id=connection.id, name="dev callback"
    )
    await db.commit()
    logger.info("store connected", extra={"store_id": token.store_id})

    return DevConnectResponse(
        connection_id=str(connection.id),
        store_id=connection.store_id,
        store_name=connection.store_name,
        scopes=connection.scopes,
        api_key=plaintext,
    )
