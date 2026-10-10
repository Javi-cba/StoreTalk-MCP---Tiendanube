import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest
from fastmcp import Client, FastMCP

from src.mcp_server import context as context_module
from src.mcp_server.context import StoreContext
from src.mcp_server.server import create_mcp
from src.services.tiendanube.client import TiendanubeClient

STORE_ID = 999
BASE_URL = f"https://api.tiendanube.com/2025-03/{STORE_ID}"
ALL_SCOPES = "read_products,write_products,read_orders,write_orders,read_coupons,write_coupons"


@dataclass
class Harness:
    mcp: FastMCP
    audits: list[dict[str, Any]] = field(default_factory=list)
    set_scopes: Callable[[str], None] = lambda _: None

    async def call(self, tool: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        async with Client(self.mcp) as client:
            result = await client.call_tool(tool, args or {})
        data: dict[str, Any] | None = result.structured_content
        assert data is not None
        return data

    async def call_error(self, tool: str, args: dict[str, Any] | None = None) -> str:
        async with Client(self.mcp) as client:
            result = await client.call_tool(tool, args or {}, raise_on_error=False)
        assert result.is_error, result
        return " ".join(getattr(c, "text", "") for c in result.content)


@pytest.fixture
async def harness(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[Harness]:
    async with httpx.AsyncClient() as http:
        state: dict[str, StoreContext] = {}

        def set_scopes(scopes: str) -> None:
            state["ctx"] = StoreContext(
                connection_id=uuid.uuid4(),
                store_id=STORE_ID,
                language="es",
                client=TiendanubeClient(http, STORE_ID, "token", scopes.split(",")),
            )

        set_scopes(ALL_SCOPES)
        h = Harness(mcp=create_mcp(auth=None), set_scopes=set_scopes)

        async def fake_context() -> StoreContext:
            return state["ctx"]

        async def fake_audit(_: StoreContext, **kwargs: Any) -> None:
            h.audits.append(kwargs)

        monkeypatch.setattr(context_module, "get_store_context", fake_context)
        monkeypatch.setattr(context_module, "record_audit", fake_audit)
        yield h
