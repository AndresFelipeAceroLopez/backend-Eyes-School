from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_by_id(self, id: int) -> T | None: ...

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]: ...

    @abstractmethod
    async def create(self, entity: dict) -> T: ...

    @abstractmethod
    async def update(self, id: int, data: dict) -> T | None: ...

    @abstractmethod
    async def delete(self, id: int) -> bool: ...
