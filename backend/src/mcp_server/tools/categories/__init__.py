"""Category tools and the category resolver."""

from fastmcp import FastMCP

from src.mcp_server.tools.categories import crud


def register(mcp: FastMCP) -> None:
    crud.register(mcp)
