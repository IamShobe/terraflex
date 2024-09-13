from contextlib import contextmanager
import pathlib
from typing import Any, Iterator, Protocol, Self, runtime_checkable

from pydantic import BaseModel

from terraflex.server.base_state_lock_provider import LockBody, LockingError
from terraflex.utils.dependency_manager import DependenciesManager

STORATE_PROVIDERS_ENTRYPOINT = "terraflex.plugins.storage_provider"


class ItemKey(BaseModel):
    def as_string(self) -> str:
        raise NotImplementedError("as_string method must be implemented in subclasses")


@runtime_checkable
class StorageProviderProtocol(Protocol):
    @classmethod
    async def from_config(
        cls,
        raw_config: Any,
        *,
        manager: DependenciesManager,
        workdir: pathlib.Path,
    ) -> Self: ...

    @classmethod
    def validate_key(cls, key: dict) -> ItemKey: ...
    # read related
    def get_file(self, item_identifier: ItemKey) -> bytes: ...


@runtime_checkable
class WriteableStorageProviderProtocol(StorageProviderProtocol, Protocol):
    # write related
    def put_file(self, item_identifier: ItemKey, data: bytes) -> None: ...
    def delete_file(self, item_identifier: ItemKey) -> None: ...


@runtime_checkable
class LockableStorageProviderProtocol(WriteableStorageProviderProtocol, Protocol):
    # lock related
    def read_lock(self, item_identifier: ItemKey) -> bytes: ...
    def acquire_lock(self, item_identifier: ItemKey, data: LockBody) -> None: ...
    def release_lock(self, item_identifier: ItemKey) -> None: ...


@contextmanager
def assume_lock_conflict_on_error(lock_id: str) -> Iterator[None]:
    try:
        yield
    except Exception as e:
        raise LockingError(
            "Failed to lock state",
            lock_id=lock_id,
        ) from e
