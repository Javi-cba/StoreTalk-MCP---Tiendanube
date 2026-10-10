"""Dev only: create a new MCP API key for an already connected store.

Usage (from backend/):  uv run python -m scripts.create_api_key <store_id> [name]
The key is printed once; only its hash is stored.
"""

import asyncio
import sys

from sqlalchemy import select

from src.config import get_settings
from src.database import engine, session_maker
from src.db.models import Connection
from src.db.repositories import create_api_key


async def main(store_id: int, name: str) -> int:
    if not get_settings().is_development:
        sys.stderr.write("Only available with ENVIRONMENT=development\n")
        return 1
    try:
        async with session_maker() as session:
            connection = await session.scalar(
                select(Connection).where(
                    Connection.store_id == store_id, Connection.revoked_at.is_(None)
                )
            )
            if connection is None:
                sys.stderr.write(f"No active connection for store {store_id}\n")
                return 1
            _, plaintext = await create_api_key(
                session, user_id=connection.user_id, connection_id=connection.id, name=name
            )
            await session.commit()
    finally:
        await engine.dispose()
    sys.stdout.write(plaintext + "\n")
    return 0


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3) or not sys.argv[1].isdigit():
        sys.stderr.write("Usage: uv run python -m scripts.create_api_key <store_id> [name]\n")
        sys.exit(2)
    key_name = sys.argv[2] if len(sys.argv) == 3 else "dev script"
    sys.exit(asyncio.run(main(int(sys.argv[1]), key_name)))
