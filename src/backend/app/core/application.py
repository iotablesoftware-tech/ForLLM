from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, Dict, Any
from dataclasses import dataclass
import datetime

T = TypeVar('T')

@dataclass(frozen=True)
class Command:
    """Marker class for all command write operations."""
    pass

@dataclass(frozen=True)
class Query(Generic[T]):
    """Marker class for all read queries returning typed values."""
    pass

class Clock(ABC):
    """Abstract provider of standardized system time across all modules."""
    @abstractmethod
    def now_utc(self) -> datetime.datetime:
        pass

class SystemClock(Clock):
    """Production system clock returning timezone-aware UTC datetime."""
    def now_utc(self) -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)

@dataclass(frozen=True)
class CurrentUser:
    """Standardized representation of the active security context."""
    id: str
    tenant_slug: Optional[str]
    roles: list[str]
    permissions: list[str]

    @property
    def is_platform_owner(self) -> bool:
        return "platform_owner" in self.roles
