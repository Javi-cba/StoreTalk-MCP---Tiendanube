import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import crypto
from src.core.api_keys import generate_api_key, hash_api_key, visible_prefix
from src.db.models import ApiKey, AuditLog, Connection, OAuthToken, User

PROVIDER_TIENDANUBE = "tiendanube"


async def get_or_create_user(
    session: AsyncSession, clerk_user_id: str, email: str | None = None
) -> User:
    user = await session.scalar(select(User).where(User.clerk_user_id == clerk_user_id))
    if user is not None:
        return user
    # ON CONFLICT: two first requests of the same Clerk user can race here.
    await session.execute(
        insert(User)
        .values(id=uuid.uuid4(), clerk_user_id=clerk_user_id, email=email)
        .on_conflict_do_nothing(index_elements=[User.clerk_user_id])
    )
    created = await session.scalar(select(User).where(User.clerk_user_id == clerk_user_id))
    assert created is not None
    return created


async def upsert_tiendanube_connection(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    store_id: int,
    access_token: str,
    scopes: str,
    store_name: str | None,
    store_language: str | None,
) -> Connection:
    """One active connection per store_id. Reinstalling refreshes the token in place.

    If the store was connected by another user, that connection (and its API keys) is revoked
    and a new one is created: whoever just authorized as store admin becomes the owner.
    """
    connection = await session.scalar(
        select(Connection).where(
            Connection.provider == PROVIDER_TIENDANUBE,
            Connection.store_id == store_id,
            Connection.revoked_at.is_(None),
        )
    )
    if connection is not None and connection.user_id != user_id:
        await revoke_connection(session, connection.id)
        connection = None
    encrypted = crypto.encrypt(access_token)
    if connection is None:
        connection = Connection(
            user_id=user_id,
            provider=PROVIDER_TIENDANUBE,
            store_id=store_id,
            access_token_encrypted=encrypted,
            key_version=crypto.CURRENT_KEY_VERSION,
            scopes=scopes,
            store_name=store_name,
            store_language=store_language,
        )
        session.add(connection)
    else:
        connection.access_token_encrypted = encrypted
        connection.key_version = crypto.CURRENT_KEY_VERSION
        connection.scopes = scopes
        connection.store_name = store_name
        connection.store_language = store_language
    await session.flush()
    return connection


async def create_api_key(
    session: AsyncSession, *, user_id: uuid.UUID, connection_id: uuid.UUID, name: str
) -> tuple[ApiKey, str]:
    """Returns the row and the plaintext key (shown only once)."""
    plaintext = generate_api_key()
    api_key = ApiKey(
        user_id=user_id,
        connection_id=connection_id,
        key_hash=hash_api_key(plaintext),
        prefix=visible_prefix(plaintext),
        name=name,
    )
    session.add(api_key)
    await session.flush()
    return api_key, plaintext


@dataclass(frozen=True)
class ResolvedApiKey:
    api_key_id: uuid.UUID
    user_id: uuid.UUID
    connection_id: uuid.UUID


async def resolve_api_key(session: AsyncSession, plaintext: str) -> ResolvedApiKey | None:
    row = await session.execute(
        select(ApiKey.id, ApiKey.user_id, ApiKey.connection_id)
        .join(Connection, Connection.id == ApiKey.connection_id)
        .where(
            ApiKey.key_hash == hash_api_key(plaintext),
            ApiKey.revoked_at.is_(None),
            Connection.revoked_at.is_(None),
        )
    )
    found = row.first()
    if found is None:
        return None
    return ResolvedApiKey(api_key_id=found[0], user_id=found[1], connection_id=found[2])


async def list_active_connections(
    session: AsyncSession, user_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[Connection], int]:
    """One page of the stores connected by the user (newest first) plus the total count."""
    active = (Connection.user_id == user_id, Connection.revoked_at.is_(None))
    total = await session.scalar(select(func.count()).select_from(Connection).where(*active))
    result = await session.scalars(
        select(Connection)
        .where(*active)
        .order_by(Connection.created_at.desc(), Connection.id)
        .limit(limit)
        .offset(offset)
    )
    return list(result), total or 0


async def get_active_connection(
    session: AsyncSession, connection_id: uuid.UUID
) -> Connection | None:
    return await session.scalar(
        select(Connection).where(Connection.id == connection_id, Connection.revoked_at.is_(None))
    )


async def get_user_connection(
    session: AsyncSession, user_id: uuid.UUID, connection_id: uuid.UUID
) -> Connection | None:
    """Active connection only if it belongs to this user (never trust the id alone)."""
    return await session.scalar(
        select(Connection).where(
            Connection.id == connection_id,
            Connection.user_id == user_id,
            Connection.revoked_at.is_(None),
        )
    )


async def revoke_connection(session: AsyncSession, connection_id: uuid.UUID) -> None:
    """Revoke the connection, its API keys and OAuth tokens, and delete the stored Tiendanube
    credentials: a revoked connection never needs its token again (reinstalling creates a new
    one)."""
    now = datetime.now(UTC)
    await session.execute(
        update(Connection)
        .where(Connection.id == connection_id, Connection.revoked_at.is_(None))
        .values(revoked_at=now, access_token_encrypted="")
    )
    await session.execute(
        update(ApiKey)
        .where(ApiKey.connection_id == connection_id, ApiKey.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    await session.execute(
        update(OAuthToken)
        .where(OAuthToken.connection_id == connection_id, OAuthToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )


async def record_audit(
    session: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    connection_id: uuid.UUID,
    tool_name: str,
    entity_type: str,
    entity_id: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> None:
    session.add(
        AuditLog(
            user_id=user_id,
            connection_id=connection_id,
            tool_name=tool_name,
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=after,
        )
    )
