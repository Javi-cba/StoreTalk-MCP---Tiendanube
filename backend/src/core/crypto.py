"""AES-256-GCM for OAuth tokens at rest. Format: base64(nonce || ciphertext)."""

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.config import get_settings

CURRENT_KEY_VERSION = 1
_NONCE_SIZE = 12


def _key(version: int) -> bytes:
    if version != CURRENT_KEY_VERSION:
        raise ValueError(f"Unknown encryption key version: {version}")
    key = base64.b64decode(get_settings().encryption_key.get_secret_value())
    if len(key) != 32:
        raise ValueError("ENCRYPTION_KEY must be 32 bytes encoded in base64")
    return key


def encrypt(plaintext: str, version: int = CURRENT_KEY_VERSION) -> str:
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = AESGCM(_key(version)).encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()


def decrypt(token: str, version: int) -> str:
    raw = base64.b64decode(token)
    nonce, ciphertext = raw[:_NONCE_SIZE], raw[_NONCE_SIZE:]
    return AESGCM(_key(version)).decrypt(nonce, ciphertext, None).decode()
