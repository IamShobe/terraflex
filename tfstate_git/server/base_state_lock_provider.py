import abc
from typing import Any, TypeAlias
from pydantic import BaseModel, ConfigDict


class LockBody(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: str
    Operation: str
    Who: str
    Version: str
    Created: str


Data: TypeAlias = Any

class LockingError(Exception):
    def __init__(self, msg: str, lock_id: str) -> None:
        super().__init__(msg)
        self.lock_id = lock_id


class BaseStateLockProvider(abc.ABC):
    @abc.abstractmethod
    async def get(self) -> Data | None: ...

    @abc.abstractmethod
    async def put(self, lock_id: str, value: Data) -> None: ...

    @abc.abstractmethod
    async def delete(self, lock_id: str) -> None: ...

    @abc.abstractmethod
    async def read_lock(self) -> LockBody | None: ...

    @abc.abstractmethod
    def lock(self, data: LockBody) -> None: ...

    @abc.abstractmethod
    def unlock(self) -> None: ...
