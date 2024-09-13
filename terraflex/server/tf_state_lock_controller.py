import json
from typing import Iterable

from terraflex.server.base_state_lock_provider import (
    StateLockProviderProtocol,
    Data,
    LockBody,
    LockingError,
)
from terraflex.server.storage_provider_base import (
    LockableStorageProviderProtocol,
    StorageProviderProtocol,
    ItemKey,
    WriteableStorageProviderProtocol,
)
from terraflex.server.transformation_base import (
    TransformerProtocol,
)


class TFStateLockController(StateLockProviderProtocol):
    def __init__(
        self,
        storage_driver: StorageProviderProtocol,
        data_transformers: Iterable[TransformerProtocol],
        state_file_storage_identifier: ItemKey,
    ):
        self.state_storage_identifier = state_file_storage_identifier
        self.storage_driver = storage_driver
        self.data_transformers = data_transformers

    async def get(self) -> Data | None:
        try:
            data = self.storage_driver.get_file(self.state_storage_identifier)

        except FileNotFoundError:
            return None

        content = data
        for transformer in self.data_transformers:
            content = await transformer.transform_read_file_content(self.state_storage_identifier.as_string(), content)

        return json.loads(content)

    async def put(self, lock_id: str, value: Data) -> None:
        if not isinstance(self.storage_driver, WriteableStorageProviderProtocol):
            raise NotImplementedError("This storage provider does not support writing")

        await self._check_lock(lock_id)
        # lock is locked by me

        data = json.dumps(value).encode()
        for transformer in self.data_transformers:
            data = await transformer.transform_write_file_content(self.state_storage_identifier.as_string(), data)

        self.storage_driver.put_file(self.state_storage_identifier, data)

    async def delete(self, lock_id: str) -> None:
        if not isinstance(self.storage_driver, WriteableStorageProviderProtocol):
            raise NotImplementedError("This storage provider does not support writing")

        await self._check_lock(lock_id)
        # lock is locked by me

        self.storage_driver.delete_file(self.state_storage_identifier)

    async def read_lock(self) -> LockBody | None:
        if not isinstance(self.storage_driver, LockableStorageProviderProtocol):
            raise NotImplementedError("This storage provider does not support writing")

        try:
            data = self.storage_driver.read_lock(self.state_storage_identifier)

        except FileNotFoundError:
            return None

        return LockBody.model_validate_json(data)

    async def _check_lock(self, lock_id: str) -> LockBody:
        if not isinstance(self.storage_driver, LockableStorageProviderProtocol):
            # This storage provider does not support locking
            return LockBody(
                ID="0000000000000000000", Operation="read", Who="me", Version="1", Created="2000-01-01T00:00:00Z"
            )

        data = await self.read_lock()
        if data is None:
            raise LockingError(
                "Failed to lock state - no lock is present",
                lock_id=lock_id,
            )

        if data.ID != lock_id:
            raise LockingError(
                "Failed to lock state - someone else has already locked it",
                lock_id=lock_id,
            )

        return data

    def lock(self, data: LockBody) -> None:
        if not isinstance(self.storage_driver, LockableStorageProviderProtocol):
            return

        self.storage_driver.acquire_lock(self.state_storage_identifier, data)

    def unlock(self) -> None:
        if not isinstance(self.storage_driver, LockableStorageProviderProtocol):
            return

        self.storage_driver.release_lock(self.state_storage_identifier)
