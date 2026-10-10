"""Resolve the store of the current MCP request. Tools never receive store_id."""

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_access_token

from src.config import get_settings
from src.core import crypto
from src.database import session_maker
from src.db.repositories import get_active_connection, revoke_connection
from src.mcp_server.auth import invalidate_cache
from src.services.tiendanube.client import TiendanubeClient, get_http_client
from src.services.tiendanube.errors import TiendanubeAuthError, TiendanubeError


@dataclass(frozen=True)
class StoreContext:
    connection_id: uuid.UUID
    store_id: int
    language: str | None
    client: TiendanubeClient


async def get_store_context() -> StoreContext:
    token = get_access_token()
    if token is None or "connection_id" not in token.claims:
        raise ToolError("No autenticado. Configurá tu API key de StoreTalk en el cliente MCP.")
    connection_id = uuid.UUID(token.claims["connection_id"])

    # Short session: read and close before calling Tiendanube.
    async with session_maker() as session:
        connection = await get_active_connection(session, connection_id)
    if connection is None:
        raise ToolError("La tienda está desconectada. Reconectala desde el dashboard.")

    access_token = crypto.decrypt(connection.access_token_encrypted, connection.key_version)
    return StoreContext(
        connection_id=connection.id,
        store_id=connection.store_id,
        language=connection.store_language,
        client=TiendanubeClient(get_http_client(), connection.store_id, access_token),
    )


async def run_tiendanube[T](ctx: StoreContext, call: Callable[[], Awaitable[T]]) -> T:
    """Apply the tool deadline and map Tiendanube errors to ToolError."""
    deadline = get_settings().tool_deadline_seconds
    try:
        async with asyncio.timeout(deadline):
            return await call()
    except TimeoutError as exc:
        raise ToolError(
            "Tiendanube tardó demasiado en responder. Probá con un filtro más acotado "
            "o una página más chica."
        ) from exc
    except TiendanubeAuthError as exc:
        async with session_maker() as session:
            await revoke_connection(session, ctx.connection_id)
            await session.commit()
        invalidate_cache()
        raise ToolError(exc.message) from exc
    except TiendanubeError as exc:
        raise ToolError(exc.message) from exc
