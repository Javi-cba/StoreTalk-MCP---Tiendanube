import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
import respx
from httpx import ASGITransport, AsyncClient

from src.auth.dependencies import get_current_user
from src.config import get_settings
from src.core import crypto
from src.database import get_db
from src.db import repositories
from src.db.models import Connection, User
from src.main import app
from src.rest import stores

USER = User(id=uuid.uuid4(), clerk_user_id="user_123")
API = f"{get_settings().tiendanube_api_base}/{get_settings().tiendanube_api_version}"


def _connection(store_id: int, name: str) -> Connection:
    return Connection(
        id=uuid.uuid4(),
        user_id=USER.id,
        provider="tiendanube",
        store_id=store_id,
        store_name=name,
        store_language="es",
        access_token_encrypted=crypto.encrypt(f"token-{store_id}"),
        key_version=crypto.CURRENT_KEY_VERSION,
        scopes="read_orders,read_products",
        created_at=datetime(2026, 10, 1, tzinfo=UTC),
    )


class FakeSession:
    async def commit(self) -> None:
        return None


@pytest.fixture
def overrides(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[uuid.UUID]]:
    live, broken = _connection(1, "Tienda viva"), _connection(2, "Tienda rota")
    revoked: list[uuid.UUID] = []

    async def fake_list(
        _: Any, user_id: uuid.UUID, *, limit: int, offset: int
    ) -> tuple[list[Connection], int]:
        assert user_id == USER.id
        connections = [live, broken]
        return connections[offset : offset + limit], len(connections)

    async def fake_revoke(_: Any, connection_id: uuid.UUID) -> None:
        revoked.append(connection_id)

    async def fake_db() -> AsyncIterator[FakeSession]:
        yield FakeSession()

    http = httpx.AsyncClient()
    monkeypatch.setattr(repositories, "list_active_connections", fake_list)
    monkeypatch.setattr(repositories, "revoke_connection", fake_revoke)
    monkeypatch.setattr(stores, "get_http_client", lambda: http)
    app.dependency_overrides[get_current_user] = lambda: USER
    app.dependency_overrides[get_db] = fake_db
    yield revoked
    app.dependency_overrides.clear()


@respx.mock
async def test_lists_live_stores_and_revokes_invalid_tokens(overrides: list[uuid.UUID]) -> None:
    respx.get(f"{API}/1/store").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 1,
                "name": {"es": "Tienda viva"},
                "main_language": "es",
                "original_domain": "viva.mitiendanube.com",
                "logo": "//cdn.example.com/logo.png",
            },
        )
    )
    respx.get(f"{API}/2/store").mock(
        return_value=httpx.Response(401, json={"description": "Invalid access token"})
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/stores")

    assert response.status_code == 200
    body = response.json()
    assert (body["page"], body["per_page"], body["total"], body["total_pages"]) == (1, 3, 1, 1)
    [store] = body["stores"]
    assert store["name"] == "Tienda viva"
    assert store["status"] == "active"
    assert store["logo_url"] == "https://cdn.example.com/logo.png"
    assert store["scopes"] == ["read_orders", "read_products"]
    assert len(overrides) == 1  # the store with an invalid token was revoked


@respx.mock
async def test_unreachable_store_falls_back_to_cached_name(overrides: list[uuid.UUID]) -> None:
    respx.get(f"{API}/1/store").mock(return_value=httpx.Response(503))
    respx.get(f"{API}/2/store").mock(return_value=httpx.Response(503))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/stores")

    names = [(s["name"], s["status"]) for s in response.json()["stores"]]
    assert names == [("Tienda viva", "unavailable"), ("Tienda rota", "unavailable")]
    assert overrides == []


@respx.mock
async def test_paginates_and_only_fetches_the_requested_page(overrides: list[uuid.UUID]) -> None:
    first = respx.get(f"{API}/1/store").mock(return_value=httpx.Response(503))
    second = respx.get(f"{API}/2/store").mock(return_value=httpx.Response(503))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/stores", params={"page": 2, "per_page": 1})

    body = response.json()
    assert [s["name"] for s in body["stores"]] == ["Tienda rota"]
    assert (body["page"], body["per_page"], body["total"], body["total_pages"]) == (2, 1, 2, 2)
    assert not first.called and second.called


async def test_rejects_out_of_range_page_size(overrides: list[uuid.UUID]) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/stores", params={"per_page": stores.MAX_PER_PAGE + 1})

    assert response.status_code == 422


DisconnectFixture = tuple[Connection, list[uuid.UUID], list[dict[str, Any]], "RecordingSession"]


class RecordingSession(FakeSession):
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True


@pytest.fixture
def disconnect_overrides(monkeypatch: pytest.MonkeyPatch) -> Iterator[DisconnectFixture]:
    connection = _connection(1, "Tienda viva")
    revoked: list[uuid.UUID] = []
    audits: list[dict[str, Any]] = []
    session = RecordingSession()

    async def fake_get(_: Any, user_id: uuid.UUID, connection_id: uuid.UUID) -> Connection | None:
        return connection if (user_id, connection_id) == (USER.id, connection.id) else None

    async def fake_revoke(_: Any, connection_id: uuid.UUID) -> None:
        revoked.append(connection_id)

    async def fake_audit(_: Any, **kwargs: Any) -> None:
        audits.append(kwargs)

    async def fake_db() -> AsyncIterator[RecordingSession]:
        yield session

    monkeypatch.setattr(repositories, "get_user_connection", fake_get)
    monkeypatch.setattr(repositories, "revoke_connection", fake_revoke)
    monkeypatch.setattr(repositories, "record_audit", fake_audit)
    app.dependency_overrides[get_current_user] = lambda: USER
    app.dependency_overrides[get_db] = fake_db
    yield connection, revoked, audits, session
    app.dependency_overrides.clear()


async def test_disconnect_revokes_and_deletes_credentials(
    disconnect_overrides: tuple[
        Connection, list[uuid.UUID], list[dict[str, Any]], RecordingSession
    ],
) -> None:
    connection, revoked, audits, session = disconnect_overrides
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(f"/api/stores/{connection.id}")

    assert response.status_code == 204
    assert revoked == [connection.id]
    assert session.committed
    assert audits[0]["tool_name"] == "disconnect_store"
    assert audits[0]["after"]["credentials_deleted"] is True


async def test_disconnect_someone_elses_store_is_404(
    disconnect_overrides: tuple[
        Connection, list[uuid.UUID], list[dict[str, Any]], RecordingSession
    ],
) -> None:
    _, revoked, _, _ = disconnect_overrides
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(f"/api/stores/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "store_not_found"
    assert revoked == []
