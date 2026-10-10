from src.core import crypto
from src.core.oauth_state import create_state, verify_state


def test_state_roundtrip() -> None:
    assert verify_state(create_state())


def test_tampered_state_is_rejected() -> None:
    assert not verify_state(create_state()[:-2] + "xx")
    assert not verify_state("garbage")


def test_token_encryption_roundtrip() -> None:
    encrypted = crypto.encrypt("secret-token")
    assert "secret-token" not in encrypted
    assert crypto.decrypt(encrypted, crypto.CURRENT_KEY_VERSION) == "secret-token"
