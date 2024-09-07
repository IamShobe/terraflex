from contextlib import contextmanager
import json
from pathlib import Path
from typing import Iterable, Iterator, override

from tfstate_git.server.base_state_lock_provider import (
    StateLockProviderProtocol,
    Data,
    LockBody,
    LockingError,
)
from tfstate_git.server.storage_providers.storage_provider_protocol import (
    StorageProviderProtocol,
)
from tfstate_git.server.transformation_providers.transformation_protocol import (
    TransformationProtocol,
)


@contextmanager
def assume_lock_conflict_on_error(lock_id: str) -> Iterator[None]:
    try:
        yield
    except Exception as e:
        raise LockingError(
            "Failed to lock state",
            lock_id=lock_id,
        ) from e


class TFStateLockController(StateLockProviderProtocol):
    def __init__(
        self,
        storage_driver: StorageProviderProtocol,
        data_transformers: Iterable[TransformationProtocol],
        state_file: Path = Path("terraform.tfstate"),
    ):
        self.state_file = state_file
        self.storage_driver = storage_driver
        self.data_transformers = data_transformers

    async def get(self) -> Data | None:
        data = self.storage_driver.get_file(str(self.state_file))
        if data is None:
            return None

        content = data
        for transformer in self.data_transformers:
            content = await transformer.transform_read_file_content(
                str(self.state_file), content
            )

        return json.loads(content)

    async def put(self, lock_id: str, value: Data) -> None:
        await self._check_lock(lock_id)
        # lock is locked by me

        data = json.dumps(value).encode()
        for transformer in self.data_transformers:
            data = await transformer.transform_write_file_content(
                str(self.state_file), data
            )

        self.storage_driver.put_file(str(self.state_file), data)

    async def delete(self, lock_id: str) -> None:
        await self._check_lock(lock_id)
        # lock is locked by me

        self.storage_driver.delete_file(str(self.state_file))

    async def read_lock(self) -> LockBody | None:
        data = self.storage_driver.read_lock(str(self.state_file))
        if data is None:
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
        self.storage_driver.acquire_lock(str(self.state_file), data)

    def unlock(self) -> None:
        self.storage_driver.release_lock(str(self.state_file))
