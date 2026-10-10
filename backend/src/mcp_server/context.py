"""Resolve the store of the current MCP request. Tools never receive store_id.

Tools call these helpers through the module (`context.get_store_context()`), so tests can
replace them in a single place.
"""

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_access_token

from src.config import get_settings
from src.core import crypto
from src.database import session_maker
from src.db import repositories
from src.mcp_server.auth import invalidate_cache
from src.services.tiendanube.client import TiendanubeClient, get_http_client
from src.services.tiendanube.errors import TiendanubeAuthError, TiendanubeError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StoreContext:
    connection_id: uuid.UUID
    store_id: int
    language: str | None
    client: TiendanubeClient
    user_id: uuid.UUID | None = None


async def get_store_context() -> StoreContext:
    token = get_access_token()
    if token is None or "connection_id" not in token.claims:
        raise ToolError("No autenticado. Configurá tu API key de StoreTalk en el cliente MCP.")
    connection_id = uuid.UUID(token.claims["connection_id"])
    user_id = token.claims.get("user_id")

    # Short session: read and close before calling Tiendanube.
    async with session_maker() as session:
        connection = await repositories.get_active_connection(session, connection_id)
    if connection is None:
        raise ToolError("La tienda está desconectada. Reconectala desde el dashboard.")

    access_token = crypto.decrypt(connection.access_token_encrypted, connection.key_version)
    return StoreContext(
        connection_id=connection.id,
        store_id=connection.store_id,
        language=connection.store_language,
        client=TiendanubeClient(
            get_http_client(), connection.store_id, access_token, connection.scopes.split(",")
        ),
        user_id=uuid.UUID(user_id) if user_id else None,
    )


async def run_tiendanube[T](ctx: StoreContext, call: Callable[[], Awaitable[T]]) -> T:
    """Apply the tool deadline and map Tiendanube errors to ToolError.

    A missing scope surfaces the exact scope to add (TiendanubeMissingScopeError message);
    only an invalid token revokes the connection.
    """
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
            await repositories.revoke_connection(session, ctx.connection_id)
            await session.commit()
        invalidate_cache()
        raise ToolError(exc.message) from exc
    except TiendanubeError as exc:
        raise ToolError(exc.message) from exc


async def record_audit(
    ctx: StoreContext,
    *,
    tool_name: str,
    entity_type: str,
    entity_id: int | str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> None:
    """Before/after snapshot of a write. Best effort: the write already happened in the store,
    so an audit failure is logged and never turned into a tool error.
    """
    try:
        async with session_maker() as session:
            await repositories.record_audit(
                session,
                user_id=ctx.user_id,
                connection_id=ctx.connection_id,
                tool_name=tool_name,
                entity_type=entity_type,
                entity_id=str(entity_id),
                before=before,
                after=after,
            )
            await session.commit()
    except Exception:
        logger.exception(
            "audit log write failed",
            extra={"connection_id": str(ctx.connection_id), "tool_name": tool_name},
        )


def remaining_budget(started_at: float) -> float:
    """Seconds left of the tool deadline (bulk tools stop early and report partial results)."""
    loop = asyncio.get_running_loop()
    return get_settings().tool_deadline_seconds - (loop.time() - started_at)
