import abc
import pathlib
from contextlib import contextmanager
from typing import Any, Iterator, Protocol, Self, TypeVar, runtime_checkable

from pydantic import BaseModel
from terraflex.server.base_state_lock_provider import LockBody, LockingError
from terraflex.utils.dependency_manager import DependenciesManager

STORATE_PROVIDERS_ENTRYPOINT = "terraflex.plugins.storage_provider"


class ItemKey(BaseModel, abc.ABC):
    """Params required to reference an item in a storage provider.

    Every storage provider must implement a subclass of `ItemKey` to represent the key of the item - using the validate_key() method.
    """

    @abc.abstractmethod
    def as_string(self) -> str:
        """Return the string representation of the key."""
        ...


T = TypeVar("T", bound=BaseModel)


def parse_item_key(item_key: ItemKey, model: type[T]) -> T:
    if not isinstance(item_key, model):
        raise ValueError(f"Item key is not of type {model}")

    return item_key


@runtime_checkable
class StorageProviderProtocol(Protocol):
    """Protocol for storage providers - Read only.

    Readable storage is the most basic storage provider - it allows to read files from the storage.

    Every readonly storage provider must implement `StorageProviderProtocol` methods -
    and register to the `terraflex.plugins.storage_provider` entrypoint.
    """

    @classmethod
    async def from_config(
        cls,
        raw_config: Any,
        *,
        manager: DependenciesManager,
        workdir: pathlib.Path,
    ) -> Self:
        """Create an instance of the storage provider from the configuration.

        Args:
            raw_config: The raw configuration propagated from the storage provider config.
            manager: The dependencies manager - allows to request a binary path from.
            workdir: The data directory of terraflex - located at `~/.local/share/terraflex` -
                can be used to manage state of the provider
        """
        ...

    @classmethod
    def validate_key(cls, key: dict[str, Any]) -> ItemKey:
        """Validate the key of the item in the storage provider from a config of usage.

        Args:
            key: a dict with parameters to build the key of the item.

        Retruns:
            The validated key.
        """
        ...

    # read related
    async def get_file(self, item_identifier: ItemKey) -> bytes:
        """Get the content of the file.

        Args:
            item_identifier: The identifier of the file.
        """
        ...


@runtime_checkable
class WriteableStorageProviderProtocol(StorageProviderProtocol, Protocol):
    """Protocol for storage providers - Writeable.

    Writeable storage provider allows to write files to the storage.

    Every writeable storage provider must implement `WriteableStorageProviderProtocol` methods and its parent methods -
        and register to the `terraflex.plugins.storage_provider` entrypoint.
    """

    # write related
    async def put_file(self, item_identifier: ItemKey, data: bytes) -> None:
        """Put the content of the file in the provided file.

        Args:
            item_identifier: The identifier of the file.
            data: The content of the file.
        """
        ...

    async def delete_file(self, item_identifier: ItemKey) -> None:
        """Delete the file.

        Args:
            item_identifier: The identifier of the file.
        """
        ...


@runtime_checkable
class LockableStorageProviderProtocol(WriteableStorageProviderProtocol, Protocol):
    """Protocol for storage providers - Lockable.

    Lockable storage provider allows to lock items to prevent concurrent writes.
    Allows to support terraform state locking - see more at official [docs](https://developer.hashicorp.com/terraform/language/state/locking).

    Every lockable storage provider must implement `LockableStorageProviderProtocol` methods and its parent methods -
        and register to the `terraflex.plugins.storage_provider` entrypoint.
    """

    # lock related
    async def read_lock(self, item_identifier: ItemKey) -> LockBody:
        """Read the lock of the item.

        Args:
            item_identifier: The identifier of the item.

        Returns:
            The lock data of the item.
        """
        ...

    async def acquire_lock(self, item_identifier: ItemKey, data: LockBody) -> None:
        """Acquire the lock of the item.

        Args:
            item_identifier: The identifier of the item.
            data: The lock data of the item.
        """
        ...

    async def release_lock(self, item_identifier: ItemKey) -> None: ...


@contextmanager
def assume_lock_conflict_on_error(lock_id: str) -> Iterator[None]:
    try:
        yield
    except Exception as e:
        raise LockingError(
            "Failed to lock state",
            lock_id=lock_id,
        ) from e
