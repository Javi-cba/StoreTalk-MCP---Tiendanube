"""Persistence of OAuth clients, authorization requests/codes and tokens."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Connection, OAuthAuthorization, OAuthClient, OAuthToken
from src.mcp_server.oauth import tokens


def _now() -> datetime:
    return datetime.now(UTC)


async def get_client(session: AsyncSession, client_id: str) -> OAuthClient | None:
    return await session.get(OAuthClient, client_id)


async def save_client(session: AsyncSession, client_id: str, info: dict[str, Any]) -> None:
    existing = await session.get(OAuthClient, client_id)
    if existing is None:
        session.add(OAuthClient(client_id=client_id, info=info))
    else:
        existing.info = info


async def create_authorization(
    session: AsyncSession, client_id: str, params: dict[str, Any]
) -> uuid.UUID:
    authorization = OAuthAuthorization(
        client_id=client_id,
        params=params,
        expires_at=_now() + timedelta(seconds=tokens.AUTHORIZATION_REQUEST_TTL_SECONDS),
    )
    session.add(authorization)
    await session.flush()
    return authorization.id


async def get_pending_authorization(
    session: AsyncSession, authorization_id: uuid.UUID
) -> tuple[OAuthAuthorization, OAuthClient] | None:
    """A request still waiting for the user's decision (no code issued yet, not expired)."""
    row = (
        await session.execute(
            select(OAuthAuthorization, OAuthClient)
            .join(OAuthClient, OAuthClient.client_id == OAuthAuthorization.client_id)
            .where(
                OAuthAuthorization.id == authorization_id,
                OAuthAuthorization.code_hash.is_(None),
                OAuthAuthorization.expires_at > _now(),
            )
        )
    ).first()
    return (row[0], row[1]) if row else None


async def approve_authorization(
    session: AsyncSession,
    authorization: OAuthAuthorization,
    *,
    user_id: uuid.UUID,
    connection_id: uuid.UUID,
) -> str:
    """Bind the request to the chosen store and return the one-time authorization code."""
    code = tokens.generate(tokens.CODE_PREFIX)
    authorization.user_id = user_id
    authorization.connection_id = connection_id
    authorization.code_hash = tokens.hash_token(code)
    authorization.expires_at = _now() + timedelta(seconds=tokens.CODE_TTL_SECONDS)
    await session.flush()
    return code


async def delete_authorization(session: AsyncSession, authorization_id: uuid.UUID) -> None:
    await session.execute(
        delete(OAuthAuthorization).where(OAuthAuthorization.id == authorization_id)
    )


async def get_authorization_by_code(
    session: AsyncSession, client_id: str, code: str
) -> OAuthAuthorization | None:
    return await session.scalar(
        select(OAuthAuthorization).where(
            OAuthAuthorization.code_hash == tokens.hash_token(code),
            OAuthAuthorization.client_id == client_id,
            OAuthAuthorization.expires_at > _now(),
        )
    )


async def consume_code(
    session: AsyncSession, client_id: str, code: str
) -> OAuthAuthorization | None:
    """Delete the code and return it: a second exchange of the same code finds nothing."""
    return await session.scalar(
        delete(OAuthAuthorization)
        .where(
            OAuthAuthorization.code_hash == tokens.hash_token(code),
            OAuthAuthorization.client_id == client_id,
            OAuthAuthorization.expires_at > _now(),
        )
        .returning(OAuthAuthorization)
    )


@dataclass(frozen=True)
class IssuedTokens:
    access_token: str
    refresh_token: str
    expires_in: int


async def issue_tokens(
    session: AsyncSession,
    *,
    client_id: str,
    user_id: uuid.UUID,
    connection_id: uuid.UUID,
    scopes: list[str],
    resource: str | None,
) -> IssuedTokens:
    grant_id = uuid.uuid4()
    now = _now()
    access = tokens.generate(tokens.ACCESS_PREFIX)
    refresh = tokens.generate(tokens.REFRESH_PREFIX)
    common = {
        "grant_id": grant_id,
        "client_id": client_id,
        "user_id": user_id,
        "connection_id": connection_id,
        "scopes": " ".join(scopes),
        "resource": resource,
    }
    session.add_all(
        [
            OAuthToken(
                token_hash=tokens.hash_token(access),
                kind="access",
                expires_at=now + timedelta(seconds=tokens.ACCESS_TOKEN_TTL_SECONDS),
                **common,
            ),
            OAuthToken(
                token_hash=tokens.hash_token(refresh),
                kind="refresh",
                expires_at=now + timedelta(seconds=tokens.REFRESH_TOKEN_TTL_SECONDS),
                **common,
            ),
        ]
    )
    await session.flush()
    return IssuedTokens(access, refresh, tokens.ACCESS_TOKEN_TTL_SECONDS)


async def get_active_token(session: AsyncSession, token: str, kind: str) -> OAuthToken | None:
    """Valid token whose store is still connected (disconnecting a store kills its tokens)."""
    return await session.scalar(
        select(OAuthToken)
        .join(Connection, Connection.id == OAuthToken.connection_id)
        .where(
            OAuthToken.token_hash == tokens.hash_token(token),
            OAuthToken.kind == kind,
            OAuthToken.revoked_at.is_(None),
            OAuthToken.expires_at > _now(),
            Connection.revoked_at.is_(None),
        )
    )


async def revoke_grant(session: AsyncSession, grant_id: uuid.UUID) -> None:
    await session.execute(
        update(OAuthToken)
        .where(OAuthToken.grant_id == grant_id, OAuthToken.revoked_at.is_(None))
        .values(revoked_at=_now())
    )
