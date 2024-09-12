from typing import Protocol, TypeAlias
from pydantic import BaseModel, ConfigDict


class LockBody(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ID: str
    Operation: str
    Who: str
    Version: str
    Created: str


Data: TypeAlias = dict


class LockingError(Exception):
    def __init__(self, msg: str, lock_id: str) -> None:
        super().__init__(msg)
        self.lock_id = lock_id


class StateLockProviderProtocol(Protocol):
    async def get(self) -> Data | None: ...
    async def put(self, lock_id: str, value: Data) -> None: ...
    async def delete(self, lock_id: str) -> None: ...
    async def read_lock(self) -> LockBody | None: ...
    def lock(self, data: LockBody) -> None: ...
    def unlock(self) -> None: ...