from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.modules.Platform.domain.models import Tenant, TenantProvisioningJob, TenantSchemaChangeJob

class TenantRepository:
    """Encapsulates transactional read and write persistence behavior for Tenant entities."""
    @staticmethod
    def get_by_id(session: Session, tenant_id: uuid.UUID) -> Optional[Tenant]:
        return session.get(Tenant, tenant_id)

    @staticmethod
    def get_by_slug(session: Session, slug: str) -> Optional[Tenant]:
        stmt = select(Tenant).where(Tenant.slug == slug)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_domain(session: Session, domain: str) -> Optional[Tenant]:
        stmt = select(Tenant).where(Tenant.domain == domain)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def add(session: Session, tenant: Tenant) -> None:
        session.add(tenant)

    @staticmethod
    def list_all(session: Session) -> List[Tenant]:
        stmt = select(Tenant).order_by(Tenant.created_at_utc.desc())
        return list(session.execute(stmt).scalars().all())


class ProvisioningJobRepository:
    """Encapsulates transactional persistence behavior for background database provisioning tasks."""
    @staticmethod
    def get_by_id(session: Session, job_id: uuid.UUID) -> Optional[TenantProvisioningJob]:
        return session.get(TenantProvisioningJob, job_id)

    @staticmethod
    def get_latest_for_tenant(session: Session, tenant_id: uuid.UUID) -> Optional[TenantProvisioningJob]:
        stmt = (
            select(TenantProvisioningJob)
            .where(TenantProvisioningJob.tenant_id == tenant_id)
            .order_by(TenantProvisioningJob.created_at_utc.desc())
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def add(session: Session, job: TenantProvisioningJob) -> None:
        session.add(job)


class SchemaChangeJobRepository:
    """Encapsulates transactional persistence behavior for background Alembic database schema migrations."""
    @staticmethod
    def get_by_id(session: Session, job_id: uuid.UUID) -> Optional[TenantSchemaChangeJob]:
        return session.get(TenantSchemaChangeJob, job_id)

    @staticmethod
    def get_latest_for_tenant(session: Session, tenant_id: uuid.UUID) -> Optional[TenantSchemaChangeJob]:
        stmt = (
            select(TenantSchemaChangeJob)
            .where(TenantSchemaChangeJob.tenant_id == tenant_id)
            .order_by(TenantSchemaChangeJob.created_at_utc.desc())
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def add(session: Session, job: TenantSchemaChangeJob) -> None:
        session.add(job)
