"""User API keys for MCP clients. Only HMAC(pepper, key) is stored."""

import hashlib
import hmac
import secrets
import string

from src.config import get_settings

KEY_PREFIX = "stk"
_ALPHABET = string.ascii_letters + string.digits
_RANDOM_LENGTH = 43  # ~256 bits in base62
_VISIBLE_PREFIX_LENGTH = len(KEY_PREFIX) + 1 + 6


def generate_api_key() -> str:
    return f"{KEY_PREFIX}_" + "".join(secrets.choice(_ALPHABET) for _ in range(_RANDOM_LENGTH))


def hash_api_key(key: str) -> str:
    pepper = get_settings().api_key_pepper.get_secret_value().encode()
    return hmac.new(pepper, key.encode(), hashlib.sha256).hexdigest()


def visible_prefix(key: str) -> str:
    return key[:_VISIBLE_PREFIX_LENGTH]
