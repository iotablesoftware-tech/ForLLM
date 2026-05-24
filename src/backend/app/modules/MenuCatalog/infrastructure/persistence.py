from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.modules.MenuCatalog.domain.models import MenuCategory, MenuItem

class MenuCategoryRepository:
    """Transactional persistence operations for MenuCategory entities."""
    @staticmethod
    def get_by_id(session: Session, category_id: uuid.UUID) -> Optional[MenuCategory]:
        return session.get(MenuCategory, category_id)

    @staticmethod
    def add(session: Session, category: MenuCategory) -> None:
        session.add(category)

    @staticmethod
    def list_all(session: Session) -> List[MenuCategory]:
        stmt = select(MenuCategory).order_by(MenuCategory.display_order, MenuCategory.name)
        return list(session.execute(stmt).scalars().all())

class MenuItemRepository:
    """Transactional persistence operations for MenuItem entities."""
    @staticmethod
    def get_by_id(session: Session, item_id: uuid.UUID) -> Optional[MenuItem]:
        return session.get(MenuItem, item_id)

    @staticmethod
    def get_by_name(session: Session, name: str) -> Optional[MenuItem]:
        stmt = select(MenuItem).where(MenuItem.name == name)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def add(session: Session, item: MenuItem) -> None:
        session.add(item)

    @staticmethod
    def list_all(session: Session) -> List[MenuItem]:
        stmt = select(MenuItem).order_by(MenuItem.name)
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def list_by_category(session: Session, category_id: uuid.UUID) -> List[MenuItem]:
        stmt = select(MenuItem).where(MenuItem.category_id == category_id).order_by(MenuItem.name)
        return list(session.execute(stmt).scalars().all())
