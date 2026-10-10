import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from httpx import ASGITransport, AsyncClient

from src.auth.dependencies import get_current_user
from src.database import get_db
from src.db.models import Connection, OAuthAuthorization, OAuthClient, User
from src.main import app
from src.rest import oauth_consent

USER = User(id=uuid.uuid4(), clerk_user_id="user_123")
STORE = Connection(
    id=uuid.uuid4(),
    user_id=USER.id,
    store_id=8331406,
    store_name="Javiis",
    scopes="read_products,write_products",
)
AUTHORIZATION = OAuthAuthorization(
    id=uuid.uuid4(),
    client_id="claude",
    params={
        "redirect_uri": "https://claude.ai/api/mcp/auth_callback",
        "redirect_uri_provided_explicitly": True,
        "state": "abc",
        "code_challenge": "challenge",
        "scopes": [],
        "resource": None,
    },
    expires_at=datetime.now(UTC) + timedelta(minutes=10),
)
CLIENT = OAuthClient(client_id="claude", info={"client_name": "Claude"})


class FakeSession:
    async def commit(self) -> None:
        return None


@pytest.fixture
def state(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[dict[str, Any]]:
    calls: dict[str, Any] = {"pending": True, "approved": None, "deleted": None}

    async def fake_pending(_: Any, authorization_id: uuid.UUID) -> Any:
        if calls["pending"] and authorization_id == AUTHORIZATION.id:
            return AUTHORIZATION, CLIENT
        return None

    async def fake_list(_: Any, user_id: uuid.UUID, *, limit: int, offset: int) -> Any:
        return [STORE], 1

    async def fake_user_connection(_: Any, user_id: uuid.UUID, connection_id: uuid.UUID) -> Any:
        return STORE if connection_id == STORE.id and user_id == USER.id else None

    async def fake_approve(_: Any, authorization: Any, **kwargs: Any) -> str:
        calls["approved"] = kwargs
        return "sto_code_123"

    async def fake_delete(_: Any, authorization_id: uuid.UUID) -> None:
        calls["deleted"] = authorization_id

    async def fake_db() -> AsyncIterator[FakeSession]:
        yield FakeSession()

    repo = oauth_consent.oauth_repository
    monkeypatch.setattr(repo, "get_pending_authorization", fake_pending)
    monkeypatch.setattr(repo, "approve_authorization", fake_approve)
    monkeypatch.setattr(repo, "delete_authorization", fake_delete)
    monkeypatch.setattr(oauth_consent.repositories, "list_active_connections", fake_list)
    monkeypatch.setattr(oauth_consent.repositories, "get_user_connection", fake_user_connection)
    app.dependency_overrides[get_current_user] = lambda: USER
    app.dependency_overrides[get_db] = fake_db
    yield calls
    app.dependency_overrides.clear()


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_shows_client_and_stores(state: dict[str, Any]) -> None:
    async with _client() as client:
        response = await client.get(f"/api/oauth/authorizations/{AUTHORIZATION.id}")

    body = response.json()
    assert response.status_code == 200
    assert body["client"] == {"name": "Claude", "redirect_host": "claude.ai"}
    assert [s["name"] for s in body["stores"]] == ["Javiis"]


async def test_approve_returns_redirect_with_code_and_state(state: dict[str, Any]) -> None:
    async with _client() as client:
        response = await client.post(
            f"/api/oauth/authorizations/{AUTHORIZATION.id}/approve",
            json={"connection_id": str(STORE.id)},
        )

    url = urlparse(response.json()["redirect_url"])
    assert (url.hostname, url.path) == ("claude.ai", "/api/mcp/auth_callback")
    assert parse_qs(url.query) == {"code": ["sto_code_123"], "state": ["abc"]}
    assert state["approved"] == {"user_id": USER.id, "connection_id": STORE.id}


async def test_cannot_approve_with_a_store_of_another_user(state: dict[str, Any]) -> None:
    async with _client() as client:
        response = await client.post(
            f"/api/oauth/authorizations/{AUTHORIZATION.id}/approve",
            json={"connection_id": str(uuid.uuid4())},
        )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "store_not_found"
    assert state["approved"] is None


async def test_expired_request_is_reported(state: dict[str, Any]) -> None:
    state["pending"] = False
    async with _client() as client:
        response = await client.get(f"/api/oauth/authorizations/{AUTHORIZATION.id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "authorization_expired"


async def test_deny_returns_access_denied(state: dict[str, Any]) -> None:
    async with _client() as client:
        response = await client.post(f"/api/oauth/authorizations/{AUTHORIZATION.id}/deny")

    query = parse_qs(urlparse(response.json()["redirect_url"]).query)
    assert query["error"] == ["access_denied"] and query["state"] == ["abc"]
    assert state["deleted"] == AUTHORIZATION.id
