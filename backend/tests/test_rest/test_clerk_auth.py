import base64
import json
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx
import jwt
import pytest
import respx
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from src.auth.clerk import (
    ClerkAuthError,
    ClerkUnavailableError,
    jwks_cache,
    verify_session_token,
)
from src.config import _issuer_from_publishable_key

ISSUER = "https://example.clerk.accounts.dev"
JWKS_URL = f"{ISSUER}/.well-known/jwks.json"
ORIGIN = "http://localhost:3000"
KID = "ins_test"

_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _jwks() -> dict[str, Any]:
    jwk = json.loads(RSAAlgorithm.to_jwk(_private_key.public_key()))
    return {"keys": [{**jwk, "kid": KID, "alg": "RS256", "use": "sig"}]}


def _token(**overrides: Any) -> str:
    now = int(time.time())
    claims = {"sub": "user_123", "sid": "sess_1", "iss": ISSUER, "azp": ORIGIN}
    claims |= {"iat": now, "nbf": now, "exp": now + 60} | overrides
    return jwt.encode(claims, _private_key, algorithm="RS256", headers={"kid": KID})


@pytest.fixture
async def http() -> AsyncIterator[httpx.AsyncClient]:
    jwks_cache.clear()
    async with httpx.AsyncClient() as client:
        yield client


async def _verify(http: httpx.AsyncClient, token: str) -> str:
    session = await verify_session_token(
        token,
        http=http,
        issuer=ISSUER,
        jwks_url=JWKS_URL,
        authorized_parties=frozenset({ORIGIN}),
    )
    return session.user_id


@respx.mock
async def test_valid_token_is_accepted_and_jwks_cached(http: httpx.AsyncClient) -> None:
    route = respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=_jwks()))
    assert await _verify(http, _token()) == "user_123"
    assert await _verify(http, _token()) == "user_123"
    assert route.call_count == 1


@respx.mock
@pytest.mark.parametrize(
    "overrides",
    [
        {"exp": int(time.time()) - 60},
        {"iss": "https://evil.clerk.accounts.dev"},
        {"azp": "https://evil.example.com"},
    ],
)
async def test_invalid_tokens_are_rejected(
    http: httpx.AsyncClient, overrides: dict[str, Any]
) -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=_jwks()))
    with pytest.raises(ClerkAuthError):
        await _verify(http, _token(**overrides))


@respx.mock
async def test_garbage_token_is_rejected(http: httpx.AsyncClient) -> None:
    with pytest.raises(ClerkAuthError):
        await _verify(http, "not-a-jwt")


@respx.mock
async def test_jwks_down_is_unavailable(http: httpx.AsyncClient) -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(503))
    with pytest.raises(ClerkUnavailableError):
        await _verify(http, _token())


def test_issuer_from_publishable_key() -> None:
    encoded = base64.b64encode(b"example.clerk.accounts.dev$").decode().rstrip("=")
    assert _issuer_from_publishable_key(f"pk_test_{encoded}") == ISSUER
