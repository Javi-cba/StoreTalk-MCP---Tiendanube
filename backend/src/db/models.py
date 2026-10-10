"""ORM models. Store data (products, orders, customers) is never persisted here."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, CreatedAtMixin


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class User(CreatedAtMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    clerk_user_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    name: Mapped[str | None] = mapped_column(String(255))

    connections: Mapped[list["Connection"]] = relationship(back_populates="user")


class Connection(CreatedAtMixin, Base):
    """A Tiendanube store connected by a user. Credentials are per store_id."""

    __tablename__ = "connections"
    __table_args__ = (
        # Only one active connection per store; revoked rows are kept for history.
        Index(
            "uq_connections_provider_store_id_active",
            "provider",
            "store_id",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="tiendanube")
    store_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    store_name: Mapped[str | None] = mapped_column(String(255))
    store_language: Mapped[str | None] = mapped_column(String(8))
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    key_version: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    scopes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="connections")


class ApiKey(CreatedAtMixin, Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("connections.id", ondelete="CASCADE"), index=True, nullable=False
    )
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    prefix: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    connection: Mapped[Connection] = relationship()


class ToolCall(CreatedAtMixin, Base):
    """Usage log. Never store full tool arguments (may contain personal data)."""

    __tablename__ = "tool_calls"
    __table_args__ = (Index("ix_tool_calls_user_id_created_at", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    api_key_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("api_keys.id", ondelete="SET NULL")
    )
    connection_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("connections.id", ondelete="SET NULL")
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)  # 'ok' | 'error'
    error_code: Mapped[str | None] = mapped_column(String(64))
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    client_name: Mapped[str | None] = mapped_column(String(100))


class AuditLog(CreatedAtMixin, Base):
    """Before/after snapshot of every write performed on a store."""

    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_connection_id_created_at", "connection_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    connection_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("connections.id", ondelete="SET NULL")
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
