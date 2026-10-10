import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import crypto
from src.core.api_keys import generate_api_key, hash_api_key, visible_prefix
from src.db.models import ApiKey, Connection, User

PROVIDER_TIENDANUBE = "tiendanube"


async def get_or_create_user(
    session: AsyncSession, clerk_user_id: str, email: str | None = None
) -> User:
    user = await session.scalar(select(User).where(User.clerk_user_id == clerk_user_id))
    if user is None:
        user = User(clerk_user_id=clerk_user_id, email=email)
        session.add(user)
        await session.flush()
    return user


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
    """One active connection per store_id. Reinstalling refreshes the token in place."""
    connection = await session.scalar(
        select(Connection).where(
            Connection.provider == PROVIDER_TIENDANUBE,
            Connection.store_id == store_id,
            Connection.revoked_at.is_(None),
        )
    )
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
        connection.user_id = user_id
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


async def get_active_connection(
    session: AsyncSession, connection_id: uuid.UUID
) -> Connection | None:
    return await session.scalar(
        select(Connection).where(Connection.id == connection_id, Connection.revoked_at.is_(None))
    )


async def revoke_connection(session: AsyncSession, connection_id: uuid.UUID) -> None:
    now = datetime.now(UTC)
    await session.execute(
        update(Connection)
        .where(Connection.id == connection_id, Connection.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    await session.execute(
        update(ApiKey)
        .where(ApiKey.connection_id == connection_id, ApiKey.revoked_at.is_(None))
        .values(revoked_at=now)
    )
