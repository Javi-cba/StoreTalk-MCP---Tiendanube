"""Consent screen of the MCP OAuth flow, called by the frontend with the Clerk session.

  GET  /api/oauth/authorizations/{id}          -> who is asking + the user's stores to choose from
  POST /api/oauth/authorizations/{id}/approve  -> binds the chosen store, returns redirect with code
  POST /api/oauth/authorizations/{id}/deny     -> returns redirect with error=access_denied

The request is created by GET /authorize (FastMCP route, see mcp_server/oauth). It expires in
15 minutes; the code issued on approval expires in 5 and can be exchanged only once.
"""

import logging
import uuid
from typing import Annotated
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, status
from mcp.server.auth.provider import construct_redirect_uri
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUser
from src.core.errors import ApiError
from src.database import get_db
from src.db import repositories
from src.db.models import OAuthAuthorization, OAuthClient
from src.mcp_server.oauth import repository as oauth_repository
from src.schemas.oauth import (
    ApproveRequest,
    AuthorizationDecision,
    AuthorizationRequestInfo,
    ConsentStore,
    OAuthClientSummary,
)
from src.schemas.stores import split_scopes

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/oauth/authorizations", tags=["oauth"])

# Enough for any merchant; the consent screen lists them all to pick one.
MAX_CONSENT_STORES = 50
DEFAULT_CLIENT_NAME = "Tu asistente de IA"


async def _pending(
    db: AsyncSession, authorization_id: uuid.UUID
) -> tuple[OAuthAuthorization, OAuthClient]:
    found = await oauth_repository.get_pending_authorization(db, authorization_id)
    if found is None:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "authorization_expired",
            "Este pedido de conexión venció o ya se usó. "
            "Volvé a conectar desde tu asistente de IA.",
        )
    return found


def _client_summary(authorization: OAuthAuthorization, client: OAuthClient) -> OAuthClientSummary:
    host = urlparse(authorization.params["redirect_uri"]).hostname or ""
    return OAuthClientSummary(
        name=client.info.get("client_name") or DEFAULT_CLIENT_NAME, redirect_host=host
    )


@router.get("/{authorization_id}", response_model=AuthorizationRequestInfo)
async def get_authorization(
    authorization_id: uuid.UUID, user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]
) -> AuthorizationRequestInfo:
    authorization, client = await _pending(db, authorization_id)
    connections, _ = await repositories.list_active_connections(
        db, user.id, limit=MAX_CONSENT_STORES, offset=0
    )
    return AuthorizationRequestInfo(
        id=authorization.id,
        client=_client_summary(authorization, client),
        stores=[
            ConsentStore(
                connection_id=c.id,
                store_id=c.store_id,
                name=c.store_name,
                scopes=split_scopes(c.scopes),
            )
            for c in connections
        ],
        expires_at=authorization.expires_at,
    )


@router.post("/{authorization_id}/approve", response_model=AuthorizationDecision)
async def approve(
    authorization_id: uuid.UUID,
    body: ApproveRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthorizationDecision:
    authorization, client = await _pending(db, authorization_id)
    connection = await repositories.get_user_connection(db, user.id, body.connection_id)
    if connection is None:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "store_not_found",
            "No encontramos esa tienda entre tus tiendas conectadas.",
        )
    code = await oauth_repository.approve_authorization(
        db, authorization, user_id=user.id, connection_id=connection.id
    )
    await db.commit()
    logger.info(
        "oauth authorization approved",
        extra={
            "user_id": str(user.id),
            "connection_id": str(connection.id),
            "client_id": client.client_id,
        },
    )
    return AuthorizationDecision(
        redirect_url=construct_redirect_uri(
            authorization.params["redirect_uri"], code=code, state=authorization.params["state"]
        )
    )


@router.post("/{authorization_id}/deny", response_model=AuthorizationDecision)
async def deny(
    authorization_id: uuid.UUID, _: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]
) -> AuthorizationDecision:
    authorization, _client = await _pending(db, authorization_id)
    await oauth_repository.delete_authorization(db, authorization.id)
    await db.commit()
    return AuthorizationDecision(
        redirect_url=construct_redirect_uri(
            authorization.params["redirect_uri"],
            error="access_denied",
            error_description="El usuario canceló la conexión.",
            state=authorization.params["state"],
        )
    )
