"""Tiendanube app installation (OAuth authorization code).

Docs: https://tiendanube.github.io/api-documentation/authentication
The redirect URL is configured only in the Partners panel (not per request).
"""

import re
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, ConfigDict, Field

from src.config import get_settings
from src.services.tiendanube.errors import TiendanubeError


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    access_token: str
    token_type: str
    scope: str = ""
    store_id: int = Field(validation_alias="user_id")


def parse_scopes(scope: str) -> list[str]:
    """Tiendanube returns the granted scopes as one string ("read_products,write_orders")."""
    return sorted({s for s in re.split(r"[,\s]+", scope) if s})


def build_authorize_url(state: str) -> str:
    settings = get_settings()
    query = urlencode({"state": state})
    return f"{settings.tiendanube_auth_base}/apps/{settings.tiendanube_client_id}/authorize?{query}"


async def exchange_code(http: httpx.AsyncClient, code: str) -> TokenResponse:
    """POST /apps/authorize/token. The code expires 5 minutes after being issued."""
    settings = get_settings()
    response = await http.post(
        f"{settings.tiendanube_auth_base}/apps/authorize/token",
        json={
            "client_id": settings.tiendanube_client_id,
            "client_secret": settings.tiendanube_client_secret.get_secret_value(),
            "grant_type": "authorization_code",
            "code": code,
        },
    )
    body = response.json() if response.content else {}
    if response.status_code >= 400 or "access_token" not in body:
        # Tiendanube returns 200 with {"error": ..., "error_description": ...} on bad codes.
        detail = body.get("error_description") or body.get("error") or response.status_code
        raise TiendanubeError(
            f"No se pudo autorizar la tienda: {detail}. El code es de un solo uso y vence a "
            "los 5 minutos (¿recargaste la página?). Volvé a iniciar la instalación."
        )
    return TokenResponse.model_validate(body)
