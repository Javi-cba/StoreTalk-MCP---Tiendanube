from fastmcp import FastMCP

from src.mcp_server.auth import ApiKeyVerifier
from src.mcp_server.tools import products


def create_mcp(auth: ApiKeyVerifier | None = None) -> FastMCP:
    server = FastMCP(
        "storetalk",
        instructions=(
            "Tools to manage the user's connected Tiendanube store. "
            "The store is resolved from the API key; never ask the user for a store id."
        ),
        auth=auth,
    )
    products.register(server)
    return server


mcp = create_mcp(auth=ApiKeyVerifier())
