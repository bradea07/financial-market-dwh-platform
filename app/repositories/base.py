from abc import ABC, abstractmethod
from typing import Generic, Iterable, TypeVar


Entity = TypeVar("Entity")
Key = TypeVar("Key")


class WarehouseRepository(ABC, Generic[Entity, Key]):
    @abstractmethod
    def save(self, entity: Entity) -> Entity:
        pass

    @abstractmethod
    def find_latest(self, partition_key: Key) -> Entity | None:
        pass

    @abstractmethod
    def find_all(self, partition_key: Key) -> Iterable[Entity]:
        pass