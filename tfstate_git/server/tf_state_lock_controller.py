import json
from typing import Iterable

from tfstate_git.server.base_state_lock_provider import (
    StateLockProviderProtocol,
    Data,
    LockBody,
    LockingError,
)
from tfstate_git.server.storage_provider_base import (
    AbstractStorageProvider,
    ItemKey,
)
from tfstate_git.server.transformation_base import (
    AbstractTransformation,
)


class TFStateLockController(StateLockProviderProtocol):
    def __init__(
        self,
        storage_driver: AbstractStorageProvider,
        data_transformers: Iterable[AbstractTransformation],
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
        await self._check_lock(lock_id)
        # lock is locked by me

        data = json.dumps(value).encode()
        for transformer in self.data_transformers:
            data = await transformer.transform_write_file_content(self.state_storage_identifier.as_string(), data)

        self.storage_driver.put_file(self.state_storage_identifier, data)

    async def delete(self, lock_id: str) -> None:
        await self._check_lock(lock_id)
        # lock is locked by me

        self.storage_driver.delete_file(self.state_storage_identifier)

    async def read_lock(self) -> LockBody | None:
        try:
            data = self.storage_driver.read_lock(self.state_storage_identifier)

        except FileNotFoundError:
            return None

        return LockBody.model_validate_json(data)

    async def _check_lock(self, lock_id: str) -> LockBody:
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
        self.storage_driver.acquire_lock(self.state_storage_identifier, data)

    def unlock(self) -> None:
        self.storage_driver.release_lock(self.state_storage_identifier)
