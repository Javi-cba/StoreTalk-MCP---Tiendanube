"""Opaque OAuth tokens and codes. Only their HMAC (same pepper as API keys) is stored."""

import secrets

from src.core.api_keys import hash_api_key

ACCESS_PREFIX = "sto_at"
REFRESH_PREFIX = "sto_rt"
CODE_PREFIX = "sto_code"

# The user has this long to pick a store in the consent screen.
AUTHORIZATION_REQUEST_TTL_SECONDS = 15 * 60
CODE_TTL_SECONDS = 5 * 60
ACCESS_TOKEN_TTL_SECONDS = 60 * 60
# Rotated on every use; a client unused for this long has to log in again.
REFRESH_TOKEN_TTL_SECONDS = 90 * 24 * 60 * 60


def generate(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def hash_token(token: str) -> str:
    return hash_api_key(token)
