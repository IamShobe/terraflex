import abc
from contextlib import contextmanager
import pathlib
from typing import Any, Iterator, Self

from pydantic import BaseModel

from tfstate_git.server.base_state_lock_provider import LockBody, LockingError
from tfstate_git.utils.dependency_manager import DependenciesManager

STORATE_PROVIDERS_ENTRYPOINT = "tfformer.plugins.storage_provider"


class ItemKey(BaseModel):
    def as_string(self) -> str:
        raise NotImplementedError("as_string method must be implemented in subclasses")


class AbstractStorageProvider(abc.ABC):
    @classmethod
    @abc.abstractmethod
    async def from_config(
        cls,
        raw_config: Any,
        *,
        manager: DependenciesManager,
        workdir: pathlib.Path,
    ) -> Self: ...

    @classmethod
    @abc.abstractmethod
    def validate_key(cls, key: dict) -> ItemKey: ...

    @abc.abstractmethod
    def get_file(self, item_identifier: ItemKey) -> bytes: ...

    @abc.abstractmethod
    def put_file(self, item_identifier: ItemKey, data: bytes) -> None: ...

    @abc.abstractmethod
    def delete_file(self, item_identifier: ItemKey) -> None: ...

    @abc.abstractmethod
    def read_lock(self, item_identifier: ItemKey) -> bytes: ...

    @abc.abstractmethod
    def acquire_lock(self, item_identifier: ItemKey, data: LockBody) -> None: ...

    @abc.abstractmethod
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
