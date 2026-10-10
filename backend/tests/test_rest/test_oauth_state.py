from src.core import crypto
from src.core.oauth_state import create_state, verify_state
from src.services.tiendanube.oauth import parse_scopes


def test_state_roundtrip() -> None:
    assert verify_state(create_state("user_a"), "user_a")


def test_tampered_state_is_rejected() -> None:
    assert not verify_state(create_state("user_a")[:-2] + "xx", "user_a")
    assert not verify_state("garbage", "user_a")


def test_state_is_bound_to_the_user() -> None:
    assert not verify_state(create_state("user_a"), "user_b")


def test_parse_scopes() -> None:
    assert parse_scopes("write_products,read_orders read_products") == [
        "read_orders",
        "read_products",
        "write_products",
    ]
    assert parse_scopes("") == []


def test_token_encryption_roundtrip() -> None:
    encrypted = crypto.encrypt("secret-token")
    assert "secret-token" not in encrypted
    assert crypto.decrypt(encrypted, crypto.CURRENT_KEY_VERSION) == "secret-token"
