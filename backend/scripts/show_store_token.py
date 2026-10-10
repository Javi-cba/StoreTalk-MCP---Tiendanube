"""Dev only: print the decrypted Tiendanube access token of a connected store.

Usage (from backend/):  uv run python -m scripts.show_store_token <store_id>
Never commit or share the output: it grants full access to the store.
"""

import asyncio
import sys

from sqlalchemy import select

from src.config import get_settings
from src.core.crypto import decrypt
from src.database import engine, session_maker
from src.db.models import Connection


async def main(store_id: int) -> int:
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
    finally:
        await engine.dispose()
    if connection is None:
        sys.stderr.write(f"No active connection for store {store_id}\n")
        return 1
    sys.stdout.write(decrypt(connection.access_token_encrypted, connection.key_version) + "\n")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        sys.stderr.write("Usage: uv run python -m scripts.show_store_token <store_id>\n")
        sys.exit(2)
    sys.exit(asyncio.run(main(int(sys.argv[1]))))
