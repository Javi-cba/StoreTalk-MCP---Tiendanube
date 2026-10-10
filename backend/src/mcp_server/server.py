from fastmcp import FastMCP

from src.mcp_server.auth import ApiKeyVerifier
from src.mcp_server.branding import server_icons
from src.mcp_server.tools import categories, coupons, orders, products


def create_mcp(auth: ApiKeyVerifier | None = None) -> FastMCP:
    server = FastMCP(
        "storetalk",
        instructions=(
            "Tools to manage the user's connected Tiendanube store. "
            "The store is resolved from the API key; never ask the user for a store id. "
            "Infer reasonable details instead of asking (e.g. adding size L to a product copies "
            "price and image from its siblings) and tell the user what was assumed. "
            "Confirm with the user before destructive tools and before applying bulk changes "
            "(run them with dry_run first). If a tool says a Tiendanube permission (scope) is "
            "missing, relay that exact scope to the user."
        ),
        auth=auth,
        icons=server_icons(),
    )
    products.register(server)
    categories.register(server)
    coupons.register(server)
    orders.register(server)
    return server


mcp = create_mcp(auth=ApiKeyVerifier())
