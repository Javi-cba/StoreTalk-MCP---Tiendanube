from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text

from src.config import get_settings
from src.core.errors import register_error_handlers
from src.core.logging import configure_logging
from src.database import engine
from src.mcp_server.server import mcp
from src.rest import stores, tiendanube_oauth
from src.services.tiendanube.client import close_http_client, create_http_client

settings = get_settings()
configure_logging(settings.log_level)

mcp_app = mcp.http_app(path="/mcp", stateless_http=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with mcp_app.lifespan(app):  # FastMCP lifespan is mandatory
        create_http_client()
        try:
            yield
        finally:
            await close_http_client()
            await engine.dispose()


app = FastAPI(title="StoreTalk API", lifespan=lifespan)
register_error_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

api_router = APIRouter()
api_router.include_router(tiendanube_oauth.router)
api_router.include_router(stores.router)
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health() -> JSONResponse:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse({"status": "degraded", "db": "down"}, status_code=503)
    return JSONResponse({"status": "ok", "db": "up"})


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    # Browsers request it automatically when opening the OAuth URLs by hand.
    return Response(status_code=204)


app.mount("/", mcp_app)  # mount last; MCP endpoint is /mcp
