"""OAuth 2.1 authorization server for MCP clients (Claude, Claude Code, ...).

The client registers itself (Dynamic Client Registration), sends the user to /authorize and
we forward the browser to the frontend consent screen ({FRONTEND_ORIGIN}/authorize), where the
user (logged in with Clerk) picks which store to share. The client then exchanges the code
(PKCE) for an access + refresh token bound to that store. Manual `stk_...` API keys keep
working as Bearer tokens.
"""

from src.mcp_server.oauth.provider import StoreTalkOAuthProvider

__all__ = ["StoreTalkOAuthProvider"]
