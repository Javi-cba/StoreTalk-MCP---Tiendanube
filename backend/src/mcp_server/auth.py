"""MCP auth: per-user API key sent as `Authorization: Bearer <api_key>`."""

import time

from fastmcp.server.auth import AccessToken, TokenVerifier

from src.core.api_keys import KEY_PREFIX, hash_api_key
from src.database import session_maker
from src.db.repositories import ResolvedApiKey, resolve_api_key

CACHE_TTL_SECONDS = 60.0

# hash(key) -> (expires_at, resolved). Hashing first so plaintext keys never sit in memory maps.
_cache: dict[str, tuple[float, ResolvedApiKey]] = {}


def invalidate_cache() -> None:
    _cache.clear()


class ApiKeyVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        if not token.startswith(f"{KEY_PREFIX}_"):
            return None
        cache_key = hash_api_key(token)
        cached = _cache.get(cache_key)
        if cached and cached[0] > time.monotonic():
            resolved = cached[1]
        else:
            async with session_maker() as session:
                found = await resolve_api_key(session, token)
            if found is None:
                _cache.pop(cache_key, None)
                return None
            resolved = found
            _cache[cache_key] = (time.monotonic() + CACHE_TTL_SECONDS, resolved)

        return AccessToken(
            token=token,
            client_id=str(resolved.user_id),
            scopes=[],
            expires_at=None,
            claims={
                "user_id": str(resolved.user_id),
                "api_key_id": str(resolved.api_key_id),
                "connection_id": str(resolved.connection_id),
            },
        )
