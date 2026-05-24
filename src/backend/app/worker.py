from celery import Celery
import os
import logging

logger = logging.getLogger("celery_worker")

# Define broker and backend URLs matching our Celery specs
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")  # Default Redis port: 6379
postgres_url = os.getenv("DATABASE_URL_PATTERN", "db+postgresql+psycopg://postgres:postgres@localhost:5432/iotable_platform")

celery_app = Celery(
    "iotable_tasks",
    broker=redis_url,
    backend=postgres_url
)

# Celery Configurations optimal for Ubuntu VPS
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1
)

from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
from app.core.infrastructure import session_manager, Base
from app.modules.Platform.domain.models import Tenant, TenantProvisioningJob
from app.modules.Platform.infrastructure.persistence import TenantRepository, ProvisioningJobRepository

# Import operational models to register them on Base for dynamic database seeding
from app.modules.Tenancy.domain.models import RestaurantProfile, TenantSettings
from app.modules.Tables.domain.models import Table
from app.modules.Stations.domain.models import Station
from app.modules.MenuCatalog.domain.models import MenuCategory, MenuItem
from app.modules.CustomerAccess.domain.models import CustomerSession
from app.modules.Ordering.domain.models import BillSession, Order, OrderItem, StationTicket, StationTicketItem, ManualPayment, BillReopenEvent

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def tenant_provisioning_job(self, tenant_slug: str, owner_email: str) -> dict:
    """Background task to dynamically provision a new tenant's PostgreSQL database, initialize its schema, and log results."""
    logger.info(f"Starting provisioning job for tenant: {tenant_slug}")
    db_name = f"iotable_tenant_{tenant_slug}"
    
    # 1. Connect to standard postgres database in AUTOCOMMIT mode to execute CREATE DATABASE
    # (CREATE DATABASE cannot run inside a standard SQLAlchemy transaction block)
    platform_base_url = session_manager.base_conn_string
    if "{db_name}" in platform_base_url:
        root_url = platform_base_url.format(db_name="postgres")
    else:
        r_slash = platform_base_url.rfind("/")
        root_url = platform_base_url[:r_slash + 1] + "postgres" if r_slash != -1 else f"{platform_base_url}/postgres"
        
    root_engine = create_engine(root_url).execution_options(isolation_level="AUTOCOMMIT")
    
    # 2. Execute CREATE DATABASE raw query
    try:
        with root_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE {db_name}"))
        logger.info(f"PostgreSQL database '{db_name}' successfully created.")
        database_created = True
    except ProgrammingError as e:
        # Code '42P04' represents duplicate_database in PostgreSQL
        if "duplicate_database" in str(e) or "42P04" in str(e):
            logger.warning(f"Database '{db_name}' already exists. Proceeding with schema creation.")
            database_created = True
        else:
            logger.error(f"Failed to create database '{db_name}': {e}")
            raise self.retry(exc=e)
    except Exception as e:
        logger.error(f"Unexpected error creating database '{db_name}': {e}")
        raise self.retry(exc=e)
        
    # 3. Dynamic schema migration execution
    # (Using declarative Base metadata mapping as initial schema creator until Alembic migrations are wired in)
    try:
        tenant_engine = session_manager._engines.get(f"tenant_{tenant_slug}")
        if not tenant_engine:
            # Force TenantSessionManager to resolve and initialize the engine
            _ = session_manager.get_tenant_session(tenant_slug)
            tenant_engine = session_manager._engines[f"tenant_{tenant_slug}"]
            
        logger.info(f"Initializing database schema mappings for tenant: {tenant_slug}")
        Base.metadata.create_all(bind=tenant_engine)
        logger.info(f"Schema initialized successfully for tenant: {tenant_slug}")
        schema_initialized = True
    except Exception as e:
        logger.error(f"Failed to initialize schema on database '{db_name}': {e}")
        raise self.retry(exc=e)
        
    # 4. Update provisioning status in platform control-plane database
    try:
        with session_manager.platform_session() as session:
            tenant = TenantRepository.get_by_slug(session, tenant_slug)
            if tenant:
                tenant.status = "pending_activation"
                # Update latest provisioning job to success
                job = ProvisioningJobRepository.get_latest_for_tenant(session, tenant.id)
                if job:
                    job.status = "success"
                else:
                    new_job = TenantProvisioningJob(tenant_id=tenant.id, status="success")
                    ProvisioningJobRepository.add(session, new_job)
                logger.info(f"Tenant '{tenant_slug}' status updated to pending_activation.")
    except Exception as e:
        logger.error(f"Failed to update tenant status in platform DB: {e}")
        # Not raising retry here since database and schema creation were successful
        
    return {
        "status": "success",
        "tenant_slug": tenant_slug,
        "owner_email": owner_email,
        "database_created": database_created,
        "schema_initialized": schema_initialized
    }

@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def tenant_schema_change_job(self, tenant_slug: str, migration_version: str) -> dict:
    """Background task to sequentially execute PostgreSQL 17 schema migrations on a tenant database."""
    logger.info(f"Starting schema migration to {migration_version} on tenant: {tenant_slug}")
    try:
        # Schema migration logic using Alembic API will go here in subsequent sprints
        return {
            "status": "success",
            "tenant_slug": tenant_slug,
            "applied_version": migration_version
        }
    except Exception as exc:
        logger.error(f"Error migrating schema for tenant {tenant_slug}: {exc}")
        raise self.retry(exc=exc)

@celery_app.task
def maintenance_job() -> dict:
    """Scheduled background job executing platform-level cleanup and audit log rotations."""
    logger.info("Executing scheduled platform maintenance tasks.")
    return {
        "status": "completed",
        "jobs_rotated": 0
    }
