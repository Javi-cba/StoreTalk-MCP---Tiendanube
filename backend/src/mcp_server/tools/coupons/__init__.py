"""Discount coupon tools."""

from fastmcp import FastMCP

from src.mcp_server.tools.coupons import crud


def register(mcp: FastMCP) -> None:
    crud.register(mcp)
