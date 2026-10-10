"""Stateless, signed OAuth `state` (CSRF protection) — no DB table needed."""

import base64
import hashlib
import hmac
import secrets
import time

from src.config import get_settings

STATE_TTL_SECONDS = 600


def _sign(payload: str) -> str:
    secret = get_settings().tiendanube_client_secret.get_secret_value().encode()
    return hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()


def create_state() -> str:
    payload = f"{int(time.time())}.{secrets.token_urlsafe(16)}"
    raw = f"{payload}.{_sign(payload)}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def verify_state(state: str) -> bool:
    try:
        padded = state + "=" * (-len(state) % 4)
        issued_at, nonce, signature = base64.urlsafe_b64decode(padded).decode().split(".")
    except (ValueError, UnicodeDecodeError):
        return False
    if not hmac.compare_digest(signature, _sign(f"{issued_at}.{nonce}")):
        return False
    return time.time() - int(issued_at) <= STATE_TTL_SECONDS
