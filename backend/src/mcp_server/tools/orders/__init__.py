"""Order tools: queries (list/get) and actions (close/reopen/cancel/note)."""

from fastmcp import FastMCP

from src.mcp_server.tools.orders import actions, queries


def register(mcp: FastMCP) -> None:
    queries.register(mcp)
    actions.register(mcp)
