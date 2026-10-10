"""FastMCP OAuthProvider backed by Postgres. Routes (/.well-known/*, /register, /authorize,
/token, /revoke) come from FastMCP; this class only stores and validates."""

import logging
from typing import Any

from fastmcp.server.auth import AccessToken
from fastmcp.server.auth.auth import OAuthProvider
from mcp.server.auth.provider import (
    AuthorizationCode,
    AuthorizationParams,
    RefreshToken,
    TokenError,
)
from mcp.server.auth.settings import ClientRegistrationOptions, RevocationOptions
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from src.core.api_keys import KEY_PREFIX
from src.database import session_maker
from src.db.models import OAuthToken as OAuthTokenRow
from src.mcp_server.auth import ApiKeyVerifier
from src.mcp_server.oauth import repository

logger = logging.getLogger(__name__)


def _timestamp(row: OAuthTokenRow) -> int | None:
    return int(row.expires_at.timestamp()) if row.expires_at else None


class StoreTalkOAuthProvider(OAuthProvider):
    def __init__(self, *, base_url: str, consent_url: str) -> None:
        super().__init__(
            base_url=base_url,
            client_registration_options=ClientRegistrationOptions(enabled=True),
            revocation_options=RevocationOptions(enabled=True),
        )
        self.consent_url = consent_url
        self._api_keys = ApiKeyVerifier()

    # --- Clients (Dynamic Client Registration) ---

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        async with session_maker() as session:
            row = await repository.get_client(session, client_id)
        return OAuthClientInformationFull.model_validate(row.info) if row else None

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        if client_info.client_id is None:
            raise ValueError("client_id is required for client registration")
        async with session_maker() as session:
            await repository.save_client(
                session, client_info.client_id, client_info.model_dump(mode="json")
            )
            await session.commit()
        logger.info(
            "oauth client registered",
            extra={"client_id": client_info.client_id, "client_name": client_info.client_name},
        )

    # --- Authorization: the user decides in the frontend consent screen ---

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        assert client.client_id is not None
        stored: dict[str, Any] = {
            "redirect_uri": str(params.redirect_uri),
            "redirect_uri_provided_explicitly": params.redirect_uri_provided_explicitly,
            "state": params.state,
            "code_challenge": params.code_challenge,
            "scopes": params.scopes or [],
            "resource": params.resource,
        }
        async with session_maker() as session:
            authorization_id = await repository.create_authorization(
                session, client.client_id, stored
            )
            await session.commit()
        return f"{self.consent_url}?request_id={authorization_id}"

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        assert client.client_id is not None
        async with session_maker() as session:
            row = await repository.get_authorization_by_code(
                session, client.client_id, authorization_code
            )
        if row is None:
            return None
        params = row.params
        return AuthorizationCode(
            code=authorization_code,
            client_id=client.client_id,
            scopes=params["scopes"],
            expires_at=row.expires_at.timestamp(),
            code_challenge=params["code_challenge"],
            redirect_uri=params["redirect_uri"],
            redirect_uri_provided_explicitly=params["redirect_uri_provided_explicitly"],
            resource=params.get("resource"),
            subject=str(row.user_id),
        )

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        assert client.client_id is not None
        async with session_maker() as session:
            row = await repository.consume_code(session, client.client_id, authorization_code.code)
            if row is None or row.user_id is None or row.connection_id is None:
                raise TokenError("invalid_grant", "Authorization code not found or already used.")
            issued = await repository.issue_tokens(
                session,
                client_id=client.client_id,
                user_id=row.user_id,
                connection_id=row.connection_id,
                scopes=authorization_code.scopes,
                resource=authorization_code.resource,
            )
            await session.commit()
        return OAuthToken(
            access_token=issued.access_token,
            token_type="Bearer",
            expires_in=issued.expires_in,
            refresh_token=issued.refresh_token,
            scope=" ".join(authorization_code.scopes) or None,
        )

    # --- Refresh (rotating) ---

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        async with session_maker() as session:
            row = await repository.get_active_token(session, refresh_token, "refresh")
        if row is None or row.client_id != client.client_id:
            return None
        return RefreshToken(
            token=refresh_token,
            client_id=row.client_id,
            scopes=row.scopes.split(),
            expires_at=_timestamp(row),
            resource=row.resource,
            subject=str(row.user_id),
        )

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        assert client.client_id is not None
        async with session_maker() as session:
            row = await repository.get_active_token(session, refresh_token.token, "refresh")
            if row is None or row.client_id != client.client_id:
                raise TokenError("invalid_grant", "Refresh token is invalid or expired.")
            granted = scopes or row.scopes.split()
            if not set(granted) <= set(row.scopes.split()):
                raise TokenError("invalid_scope", "Requested scopes exceed the original grant.")
            # Rotation: the old pair stops working as soon as the new one is issued.
            await repository.revoke_grant(session, row.grant_id)
            issued = await repository.issue_tokens(
                session,
                client_id=client.client_id,
                user_id=row.user_id,
                connection_id=row.connection_id,
                scopes=granted,
                resource=row.resource,
            )
            await session.commit()
        return OAuthToken(
            access_token=issued.access_token,
            token_type="Bearer",
            expires_in=issued.expires_in,
            refresh_token=issued.refresh_token,
            scope=" ".join(granted) or None,
        )

    # --- Access tokens (and manual API keys) ---

    async def load_access_token(self, token: str) -> AccessToken | None:
        # Manual `stk_...` keys (Claude Desktop config, Claude Code --header) keep working.
        if token.startswith(f"{KEY_PREFIX}_"):
            return await self._api_keys.verify_token(token)
        async with session_maker() as session:
            row = await repository.get_active_token(session, token, "access")
        if row is None:
            return None
        return AccessToken(
            token=token,
            client_id=row.client_id,
            scopes=row.scopes.split(),
            expires_at=_timestamp(row),
            resource=row.resource,
            subject=str(row.user_id),
            claims={
                "user_id": str(row.user_id),
                "connection_id": str(row.connection_id),
                "oauth_client_id": row.client_id,
            },
        )

    async def verify_token(self, token: str) -> AccessToken | None:
        return await self.load_access_token(token)

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        kind = "refresh" if isinstance(token, RefreshToken) else "access"
        async with session_maker() as session:
            row = await repository.get_active_token(session, token.token, kind)
            if row is not None:
                await repository.revoke_grant(session, row.grant_id)
                await session.commit()
