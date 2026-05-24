import sys
import os

# Append src/backend to python path so imports resolve cleanly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/backend")))

from app.core.infrastructure import session_manager, Base
from app.modules.Platform.domain.models import Tenant, TenantProvisioningJob
from app.modules.Platform.infrastructure.persistence import TenantRepository, ProvisioningJobRepository
from app.worker import tenant_provisioning_job

def main():
    print("Connecting to central platform database...")
    _ = session_manager.get_platform_session()
    platform_engine = session_manager._engines["platform"]
    
    print("Creating central platform schemas...")
    Base.metadata.create_all(bind=platform_engine)
    print("Central platform tables created successfully.")
    
    with session_manager.platform_session() as session:
        existing = session.query(Tenant).filter_by(slug="demo1").first()
        if not existing:
            print("Registering tenant 'demo1'...")
            tenant = Tenant(slug="demo1", domain="demo1.iotables.net", status="draft")
            TenantRepository.add(session, tenant)
            session.commit()
            
            job = TenantProvisioningJob(tenant_id=tenant.id, status="queued")
            ProvisioningJobRepository.add(session, job)
            session.commit()
            
            print("Running provisioning Celery task synchronously for 'demo1'...")
            prov_result = tenant_provisioning_job("demo1", "owner@demo1.iotables.net")
            print("Provisioning completed successfully:", prov_result)
        else:
            print("Tenant 'demo1' already registered.")

if __name__ == "__main__":
    main()
