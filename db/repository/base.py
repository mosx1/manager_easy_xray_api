from typing import TypeVar, Generic, Any, Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session
from abc import ABC, abstractmethod
from db.db import get_session

T = TypeVar('T')  # Generic тип для модели SQLAlchemy

class AbstractRepository(ABC, Generic[T]):
    """Абстрактный базовый класс репозитория для работы с БД"""
    
    def __init__(self):
        """Инициализация репозитория с сессией SQLAlchemy"""
        self.session: Session = get_session()

    @property
    @abstractmethod
    def model(self) -> type[T]:
        """Возвращает класс модели SQLAlchemy"""
        pass
    
    def create(self, entity: T) -> T:
        """Создание новой записи"""
        self.session.add(entity)
        self.session.flush()
        self.session.refresh(entity)
        return entity
    
    def get_by_id(self, id: Any) -> Optional[T]:
        """Получение записи по первичному ключу"""
        return self.session.get(self.model, id)
    

    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """
            Получение всех записей с пагинацией
        """
        stmt = select(self.model)

        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)

        result = self.session.execute(stmt)

        return result.scalars().all()
    

    def update(self, id: Any, update_data: dict) -> Optional[T]:
        """Обновление записи"""
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
            .returning(self.model)
        )
        result = self.session.execute(stmt)  # noqa: F811
        return result.scalar_one_or_none()
    
    def update_by_filter(self, filters: list, update_data: dict) -> None:
        """
            Обновление записей по фильтру
        """
        stmt = (
            update(self.model)
            .where(*filters)
            .values(**update_data)
        )
        self.session.execute(stmt)
    
    def delete(self, id: Any) -> bool:
        """Удаление записи"""
        stmt = delete(self.model).where(self.model.id == id)
        result = self.session.execute(stmt)
        return result.rowcount > 0
    
    def filter(self, **filters) -> List[T]:
        """Фильтрация записей по параметрам"""
        stmt = select(self.model).filter_by(*filters)
        result = self.session.execute(stmt)
        return result.scalars().all()
    
    def get_one(self, filter) -> Optional[T]:
        """Получение одной записи по фильтру"""
        stmt = select(self.model).filter(filter).limit(1)
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()


class BaseRepository(AbstractRepository[T]):

    def __init__(self, model: type[T]):
        super().__init__()
        self._model = model

    def __enter__(self):
        return self
    
    def __exit__(self, _type, _val, _tb):
        try:
            if _type is not None:
                self.session.rollback()
        finally:
            self.session.close()
        return False
    
    @property
    def model(self) -> type[T]:
        return self._model