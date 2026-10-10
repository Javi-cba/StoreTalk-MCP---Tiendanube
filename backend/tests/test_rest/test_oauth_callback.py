from httpx import ASGITransport, AsyncClient

from src.main import app


async def test_callback_forwards_code_and_state_to_frontend() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/tiendanube/callback", params={"code": "abc", "state": "s1", "extra": "x"}
        )
    assert response.status_code == 303
    assert response.headers["location"] == (
        "http://localhost:3000/connect/callback?code=abc&state=s1"
    )


async def test_callback_without_code_still_lands_on_frontend() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/tiendanube/callback")
    assert response.headers["location"] == "http://localhost:3000/connect/callback"
