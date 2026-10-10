from fastmcp import FastMCP
from fastmcp.server.auth import AuthProvider

from src.config import get_settings
from src.mcp_server.branding import server_icons
from src.mcp_server.oauth import StoreTalkOAuthProvider
from src.mcp_server.tools import categories, coupons, orders, products


def create_mcp(auth: AuthProvider | None = None) -> FastMCP:
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


def create_auth() -> StoreTalkOAuthProvider:
    """OAuth for clients that add the server by URL (Claude connectors, Claude Code) plus manual
    `stk_...` API keys. PUBLIC_BASE_URL is the issuer: the ngrok tunnel locally, the domain when
    hosted. The consent screen lives in the frontend."""
    settings = get_settings()
    return StoreTalkOAuthProvider(
        base_url=settings.public_base_url.rstrip("/"),
        consent_url=f"{settings.frontend_origin.rstrip('/')}/authorize",
    )


mcp = create_mcp(auth=create_auth())
