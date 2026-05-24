from typing import Generic, TypeVar, Optional, Any, Union, List
from dataclasses import dataclass, field
import datetime

T = TypeVar('T')
E = TypeVar('E', bound=Exception)

class DomainException(Exception):
    """Base exception class for all IoTable business domain rule violations."""
    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.code = code or "DOMAIN_RULE_VIOLATION"

@dataclass(frozen=True)
class ValueObject:
    """Base class for all immutable value objects in the domain model."""
    def __eq__(self, other: Any) -> bool:
        if type(other) is not type(self):
            return False
        return self.__dict__ == other.__dict__

class Entity(Generic[T]):
    """Base class for all identifiable entities in the domain model."""
    def __init__(self, id: T):
        if id is None:
            raise DomainException("Entity identifier cannot be null", "NULL_ENTITY_ID")
        self.id: T = id

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Entity):
            return False
        if type(self) is not type(other):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

@dataclass
class DomainEvent:
    """Base class for all transactional domain events emitted by modules."""
    occurred_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

class Result(Generic[T]):
    """Monadic result pattern wrapping successful data or domain errors."""
    def __init__(self, is_success: bool, value: Optional[T] = None, error: Optional[str] = None, error_code: Optional[str] = None):
        self.is_success = is_success
        self._value = value
        self.error = error
        self.error_code = error_code

    @property
    def value(self) -> T:
        if not self.is_success:
            raise DomainException(f"Cannot access value of a failed result: {self.error}", self.error_code)
        return self._value  # type: ignore

    @classmethod
    def success(cls, value: T) -> 'Result[T]':
        return cls(is_success=True, value=value)

    @classmethod
    def fail(cls, error: str, error_code: str = "OPERATION_FAILED") -> 'Result[Any]':
        return cls(is_success=False, error=error, error_code=error_code)
