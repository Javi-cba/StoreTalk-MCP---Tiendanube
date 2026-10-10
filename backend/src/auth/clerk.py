"""Local verification of Clerk session JWTs against the instance JWKS (no network per request).

Docs: https://clerk.com/docs/guides/sessions/manual-jwt-verification
"""

import asyncio
import logging
import time
from dataclasses import dataclass

import httpx
import jwt
from jwt import PyJWK

logger = logging.getLogger(__name__)

JWKS_TTL_SECONDS = 3600.0
# Unknown `kid` triggers a refetch, but never more often than this (avoids hammering Clerk).
MIN_REFRESH_INTERVAL_SECONDS = 30.0
LEEWAY_SECONDS = 5


class ClerkAuthError(Exception):
    """The token is missing, malformed, expired or not issued for us."""


class ClerkUnavailableError(Exception):
    """The JWKS could not be fetched, so the token cannot be verified right now."""


@dataclass(frozen=True)
class ClerkSession:
    user_id: str
    session_id: str | None


class JwksCache:
    def __init__(self) -> None:
        self._keys: dict[str, PyJWK] = {}
        self._fetched_at = 0.0
        self._lock = asyncio.Lock()

    def clear(self) -> None:
        self._keys = {}
        self._fetched_at = 0.0

    async def get_key(self, http: httpx.AsyncClient, url: str, kid: str) -> PyJWK:
        age = time.monotonic() - self._fetched_at
        expired = not self._keys or age > JWKS_TTL_SECONDS
        if expired or (kid not in self._keys and age > MIN_REFRESH_INTERVAL_SECONDS):
            await self._refresh(http, url, force=expired)
        key = self._keys.get(kid)
        if key is None:
            raise ClerkAuthError("unknown signing key")
        return key

    async def _refresh(self, http: httpx.AsyncClient, url: str, *, force: bool) -> None:
        async with self._lock:
            # Another request may have refreshed while we waited for the lock.
            if not force and time.monotonic() - self._fetched_at < MIN_REFRESH_INTERVAL_SECONDS:
                return
            try:
                response = await http.get(url)
                response.raise_for_status()
                payload = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                logger.warning("clerk jwks fetch failed", extra={"error": type(exc).__name__})
                if self._keys:
                    return  # keep serving the previous keys
                raise ClerkUnavailableError from exc
            keys: dict[str, PyJWK] = {}
            for data in payload.get("keys", []):
                try:
                    key = PyJWK(data)
                except jwt.PyJWTError:
                    continue
                if key.key_id:
                    keys[key.key_id] = key
            self._keys = keys
            self._fetched_at = time.monotonic()


jwks_cache = JwksCache()


async def verify_session_token(
    token: str,
    *,
    http: httpx.AsyncClient,
    issuer: str,
    jwks_url: str,
    authorized_parties: frozenset[str],
) -> ClerkSession:
    try:
        kid = jwt.get_unverified_header(token).get("kid")
    except jwt.PyJWTError as exc:
        raise ClerkAuthError("malformed token") from exc
    if not isinstance(kid, str):
        raise ClerkAuthError("token without kid")

    key = await jwks_cache.get_key(http, jwks_url, kid)
    try:
        claims = jwt.decode(
            token,
            key=key.key,
            algorithms=["RS256"],
            issuer=issuer,
            leeway=LEEWAY_SECONDS,
            options={"require": ["exp", "iat", "iss", "sub"], "verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        raise ClerkAuthError(type(exc).__name__) from exc

    # Clerk sets `azp` to the origin that requested the token; reject other frontends.
    azp = claims.get("azp")
    if azp is not None and str(azp).rstrip("/") not in authorized_parties:
        raise ClerkAuthError("unauthorized party")

    session_id = claims.get("sid")
    return ClerkSession(
        user_id=str(claims["sub"]),
        session_id=session_id if isinstance(session_id, str) else None,
    )
