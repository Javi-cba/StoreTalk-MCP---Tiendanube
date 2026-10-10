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
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
