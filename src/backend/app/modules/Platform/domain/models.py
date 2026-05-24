import uuid
import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.infrastructure import Base

class Tenant(Base):
    """Platform-level registry representing isolated tenant SaaS accounts."""
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(63), unique=True, nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    
    # Statuses: draft, provisioning, provisioning_failed, pending_activation, active, suspended, deactivated
    status: Mapped[str] = mapped_column(String(31), default="draft", nullable=False)
    
    created_at_utc: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.datetime.now(datetime.timezone.utc), 
        nullable=False
    )
    updated_at_utc: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False
    )

    # Relationships
    provisioning_jobs: Mapped[list["TenantProvisioningJob"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    schema_change_jobs: Mapped[list["TenantSchemaChangeJob"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tenant slug={self.slug} status={self.status}>"


class TenantProvisioningJob(Base):
    """Tracks background provisioning jobs executed via Celery to isolate and seed tenant resources."""
    __tablename__ = "tenant_provisioning_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    # Statuses: queued, running, success, failed
    status: Mapped[str] = mapped_column(String(31), default="queued", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at_utc: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.datetime.now(datetime.timezone.utc), 
        nullable=False
    )
    updated_at_utc: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="provisioning_jobs")

    def __repr__(self) -> str:
        return f"<TenantProvisioningJob id={self.id} status={self.status}>"


class TenantSchemaChangeJob(Base):
    """Tracks background Alembic dynamic migration schema upgrades executed on dynamic tenant databases."""
    __tablename__ = "tenant_schema_change_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    migration_version: Mapped[str] = mapped_column(String(63), nullable=False)
    
    # Statuses: queued, running, success, failed
    status: Mapped[str] = mapped_column(String(31), default="queued", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at_utc: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.datetime.now(datetime.timezone.utc), 
        nullable=False
    )
    updated_at_utc: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="schema_change_jobs")

    def __repr__(self) -> str:
        return f"<TenantSchemaChangeJob version={self.migration_version} status={self.status}>"
