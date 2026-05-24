from typing import Dict, Generator, Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import os
import contextlib

Base = declarative_base()

class TenantSessionManager:
    """Manages dynamic connection pool routing per tenant for PostgreSQL 17 database isolation."""
    def __init__(self, base_conn_string: Optional[str] = None):
        # Fallback to local default development PostgreSQL string if env is not defined
        self.base_conn_string = base_conn_string or os.getenv(
            "DATABASE_URL_PATTERN", 
            "postgresql+psycopg://postgres:postgres@localhost:5432/{db_name}"
        )
        self._engines: Dict[str, Engine] = {}
        self._sessionmakers: Dict[str, sessionmaker[Session]] = {}
        # Platform engine is initialized lazily on first use to avoid import-time crashes

    def _init_engine(self, key: str, db_name: str) -> None:
        if "{db_name}" in self.base_conn_string:
            conn_str = self.base_conn_string.format(db_name=db_name)
        else:
            # Dynamically replace trailing database name in standard connection URL
            r_slash = self.base_conn_string.rfind("/")
            if r_slash != -1:
                # Keep everything up to the slash and append the target database name
                conn_str = self.base_conn_string[:r_slash + 1] + db_name
            else:
                conn_str = f"{self.base_conn_string}/{db_name}"
        
        # Configure pooling standard optimal for VPS hosting
        engine = create_engine(
            conn_str,
            pool_size=10,
            max_overflow=5,
            pool_recycle=1800,
            pool_pre_ping=True
        )
        self._engines[key] = engine
        self._sessionmakers[key] = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def get_platform_session(self) -> Session:
        """Returns a transactional session bound to the central platform control-plane database."""
        if "platform" not in self._engines:
            self._init_engine("platform", "iotable_platform")
        return self._sessionmakers["platform"]()

    def get_tenant_session(self, tenant_slug: str) -> Session:
        """Resolves database engine dynamically and returns a session isolated for the given tenant."""
        if not tenant_slug:
            raise ValueError("Tenant slug is required for tenant database session resolution.")
            
        key = f"tenant_{tenant_slug}"
        if key not in self._engines:
            # Construct standard tenant database name pattern matching spec: iotable_tenant_{tenantSlug}
            db_name = f"iotable_tenant_{tenant_slug}"
            self._init_engine(key, db_name)
            
        return self._sessionmakers[key]()

    @contextlib.contextmanager
    def platform_session(self) -> Generator[Session, None, None]:
        """Transactional context manager for the platform database."""
        session = self.get_platform_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextlib.contextmanager
    def tenant_session(self, tenant_slug: str) -> Generator[Session, None, None]:
        """Transactional context manager for dynamic tenant database isolation."""
        session = self.get_tenant_session(tenant_slug)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

# Singleton instance of Session Manager
session_manager = TenantSessionManager()
