from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import get_settings

_settings = get_settings()

# Neon pooler = PgBouncer in transaction mode -> disable psycopg prepared statements.
engine: AsyncEngine = create_async_engine(
    _settings.async_database_url,
    connect_args={"prepare_threshold": None},
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=300,
)

session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with session_maker() as session:
        yield session
