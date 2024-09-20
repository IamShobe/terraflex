from typing import Protocol, TypeAlias
from pydantic import BaseModel, ConfigDict


class LockBody(BaseModel):
    """Data struct that contains the lock information.

    This is the same data struct that is required by terraform.
    It follows the same fields names as the terraform lock file.

    See offical [source](https://github.com/hashicorp/terraform/blob/aea5c0cc180e0e6915454b3bf61f471c230c111b/internal/states/statemgr/locker.go#L129).

    Attributes:
        ID: The ID of the lock.
        Operation: The operation that is being performed.
        Who: The entity that is performing the operation.
        Version: The version of the lock.
        Created: The time when the lock was created.
    """

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
    async def get(self, stack_name: str) -> Data | None: ...
    async def put(self, stack_name: str, lock_id: str, value: Data) -> None: ...
    async def delete(self, stack_name: str, lock_id: str) -> None: ...
    async def read_lock(self, stack_name: str) -> LockBody | None: ...
    async def lock(self, stack_name: str, data: LockBody) -> None: ...
    async def unlock(self, stack_name: str) -> None: ...
