"""Consent screen of the MCP OAuth flow ({FRONTEND_ORIGIN}/authorize?request_id=...)."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class OAuthClientSummary(BaseModel):
    name: str
    # Host the browser returns to after approving (e.g. claude.ai). Shown so the user can spot
    # an unexpected client before sharing a store.
    redirect_host: str


class ConsentStore(BaseModel):
    connection_id: uuid.UUID
    store_id: int
    name: str | None
    scopes: list[str]


class AuthorizationRequestInfo(BaseModel):
    id: uuid.UUID
    client: OAuthClientSummary
    stores: list[ConsentStore]
    expires_at: datetime


class ApproveRequest(BaseModel):
    connection_id: uuid.UUID


class AuthorizationDecision(BaseModel):
    """Where the frontend sends the browser next (the MCP client's redirect_uri)."""

    redirect_url: str
