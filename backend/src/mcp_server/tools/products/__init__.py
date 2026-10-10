"""Catalog tools: products, variants, images and bulk pricing."""

from fastmcp import FastMCP

from src.mcp_server.tools.products import crud, images, pricing, variants


def register(mcp: FastMCP) -> None:
    crud.register(mcp)
    variants.register(mcp)
    images.register(mcp)
    pricing.register(mcp)
