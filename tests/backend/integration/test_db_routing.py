import pytest
import uuid
from sqlalchemy import create_engine, text
from app.core.infrastructure import session_manager, Base
from app.modules.Platform.domain.models import Tenant, TenantProvisioningJob
from app.modules.Platform.infrastructure.persistence import TenantRepository, ProvisioningJobRepository
from app.worker import tenant_provisioning_job

def test_tenant_session_manager_and_provisioning_end_to_end():
    """Validates dynamic connection pooling, dynamic postgres database creation, and dynamic schema initialization."""
    # Ensure platform database is initialized and tables exist
    platform_engine = session_manager._engines.get("platform")
    if not platform_engine:
        # Force session manager to resolve the platform session
        _ = session_manager.get_platform_session()
        platform_engine = session_manager._engines["platform"]

    # Initialize platform tables (Tenant, Jobs) in the platform database
    Base.metadata.create_all(bind=platform_engine)

    test_slug = f"test_{uuid.uuid4().hex[:8]}"
    test_domain = f"{test_slug}.iotables.net"
    owner_email = "owner@test.com"

    # 1. Create a Tenant in draft status inside the Platform database
    with session_manager.platform_session() as session:
        # Clean up any existing tenant with this slug
        existing = TenantRepository.get_by_slug(session, test_slug)
        if existing:
            session.delete(existing)
            session.commit()
            
        tenant = Tenant(slug=test_slug, domain=test_domain, status="draft")
        TenantRepository.add(session, tenant)
        session.commit()
        tenant_id = tenant.id

        # Insert a queued provisioning job
        job = TenantProvisioningJob(tenant_id=tenant_id, status="queued")
        ProvisioningJobRepository.add(session, job)
        session.commit()

    # 2. Run the dynamic provisioning job synchronously to create the new Postgres database
    result = tenant_provisioning_job(test_slug, owner_email)
    
    assert result["status"] == "success"
    assert result["tenant_slug"] == test_slug
    assert result["database_created"] is True
    assert result["schema_initialized"] is True

    # 3. Verify that the Tenant's status was updated to pending_activation and the job status is success
    with session_manager.platform_session() as session:
        updated_tenant = TenantRepository.get_by_slug(session, test_slug)
        assert updated_tenant is not None
        assert updated_tenant.status == "pending_activation"

        job = ProvisioningJobRepository.get_latest_for_tenant(session, tenant_id)
        assert job is not None
        assert job.status == "success"

    # 4. Verify that we can dynamically open a connection session for the new tenant database and execute queries
    db_name = f"iotable_tenant_{test_slug}"
    try:
        with session_manager.tenant_session(test_slug) as tenant_session:
            # Query standard PostgreSQL table to ensure schema created successfully
            # Platform jobs table should NOT exist in tenant DB, but we check if we can connect
            tenant_session.execute(text("SELECT 1"))
        routing_success = True
    except Exception as e:
        routing_success = False
        print(f"Routing to tenant database failed: {e}")
    
    assert routing_success is True

    # 5. Clean up by dropping the dynamically created tenant database
    platform_base_url = session_manager.base_conn_string
    if "{db_name}" in platform_base_url:
        root_url = platform_base_url.format(db_name="postgres")
    else:
        r_slash = platform_base_url.rfind("/")
        root_url = platform_base_url[:r_slash + 1] + "postgres" if r_slash != -1 else f"{platform_base_url}/postgres"
        
    root_engine = create_engine(root_url).execution_options(isolation_level="AUTOCOMMIT")
    with root_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE {db_name} (FORCE)"))
        
    # Clean up Platform DB row
    with session_manager.platform_session() as session:
        t = TenantRepository.get_by_slug(session, test_slug)
        if t:
            session.delete(t)
