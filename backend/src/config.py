import base64
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent

# Local dev: the monorepo root .env is shared by backend and frontend.
# Deploy: if the platform builds only /backend, a backend/.env (or real env vars) is used.
# Later files win over earlier ones; real environment variables win over all files.
ENV_FILES: tuple[Path, ...] = (ROOT_DIR / ".env", BACKEND_DIR / ".env")


def _to_psycopg_url(url: str) -> str:
    for prefix in ("postgresql+psycopg://", "postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


def _issuer_from_publishable_key(key: str) -> str | None:
    """pk_(test|live)_<base64("<frontend-api-host>$")> -> https://<frontend-api-host>."""
    encoded = key.split("_", 2)[-1]
    try:
        host = base64.b64decode(encoded + "=" * (-len(encoded) % 4)).decode().rstrip("$")
    except (ValueError, UnicodeDecodeError):
        return None
    return f"https://{host}" if host else None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILES, extra="ignore")

    # Server
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    tool_deadline_seconds: float = 20.0
    frontend_origin: str = "http://localhost:3000"
    public_base_url: str = "http://localhost:8000"

    # Database (Neon)
    database_url: str
    database_url_direct: str | None = None

    # Encryption / API keys
    encryption_key: SecretStr
    api_key_pepper: SecretStr

    # Tiendanube
    tiendanube_client_id: str = Field(
        validation_alias=AliasChoices("TIENDANUBE_CLIENT_ID", "TIENDANUBE_APP_ID")
    )
    tiendanube_client_secret: SecretStr
    tiendanube_user_agent: str
    tiendanube_api_base: str = "https://api.tiendanube.com"
    tiendanube_api_version: str = "2025-03"
    tiendanube_auth_base: str = "https://www.tiendanube.com"

    # Clerk. Issuer and JWKS URL are derived from the publishable key unless set explicitly.
    clerk_publishable_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CLERK_PUBLISHABLE_KEY", "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"),
    )
    clerk_issuer: str | None = None
    clerk_jwks_url: str | None = None
    # Comma-separated origins allowed in the `azp` claim. Defaults to FRONTEND_ORIGIN.
    clerk_authorized_parties: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        """Pooled URL used by the app."""
        return _to_psycopg_url(self.database_url)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def migrations_database_url(self) -> str:
        """Direct (non-pooler) URL used by Alembic. Falls back to stripping '-pooler'."""
        url = self.database_url_direct or self.database_url.replace("-pooler.", ".")
        return _to_psycopg_url(url)

    @property
    def clerk_issuer_url(self) -> str | None:
        if self.clerk_issuer:
            return self.clerk_issuer.rstrip("/")
        if self.clerk_publishable_key:
            return _issuer_from_publishable_key(self.clerk_publishable_key)
        return None

    @property
    def clerk_jwks_endpoint(self) -> str | None:
        if self.clerk_jwks_url:
            return self.clerk_jwks_url
        issuer = self.clerk_issuer_url
        return f"{issuer}/.well-known/jwks.json" if issuer else None

    @property
    def clerk_allowed_parties(self) -> frozenset[str]:
        raw = self.clerk_authorized_parties or self.frontend_origin
        return frozenset(origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip())

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
