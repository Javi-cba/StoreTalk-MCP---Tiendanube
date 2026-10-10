"""FastAPI dependencies for REST routes authenticated with a Clerk session JWT."""

import logging
from typing import Annotated

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.clerk import (
    ClerkAuthError,
    ClerkSession,
    ClerkUnavailableError,
    verify_session_token,
)
from src.config import get_settings
from src.core.errors import ApiError
from src.database import get_db
from src.db import repositories
from src.db.models import User
from src.services.tiendanube.client import get_http_client

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


async def get_clerk_session(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> ClerkSession:
    """Verifies the JWT only (no DB). Use it in routes that call Tiendanube before touching
    the DB, so no connection is held while waiting on external APIs."""
    if credentials is None:
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED, "unauthenticated", "Iniciá sesión para continuar."
        )
    settings = get_settings()
    issuer, jwks_url = settings.clerk_issuer_url, settings.clerk_jwks_endpoint
    if issuer is None or jwks_url is None:
        logger.error("clerk is not configured (CLERK_PUBLISHABLE_KEY / CLERK_ISSUER missing)")
        raise ApiError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "auth_unavailable",
            "El inicio de sesión no está disponible en este momento.",
        )
    try:
        return await verify_session_token(
            credentials.credentials,
            http=get_http_client(),
            issuer=issuer,
            jwks_url=jwks_url,
            authorized_parties=settings.clerk_allowed_parties,
        )
    except ClerkAuthError as exc:
        logger.info("rejected clerk token", extra={"error": str(exc)})
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "invalid_session",
            "Tu sesión venció o no es válida. Volvé a iniciar sesión.",
        ) from exc
    except ClerkUnavailableError as exc:
        raise ApiError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "auth_unavailable",
            "No pudimos validar tu sesión. Probá de nuevo en unos segundos.",
        ) from exc


CurrentSession = Annotated[ClerkSession, Depends(get_clerk_session)]


async def get_current_user(
    session: CurrentSession, db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """Maps the Clerk `sub` to our users table (created on first request)."""
    user = await repositories.get_or_create_user(db, session.user_id)
    await db.commit()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
