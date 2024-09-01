import abc
from contextlib import contextmanager
import json
import pathlib

from tfstate_git.server.base_state_lock_provider import (
    BaseStateLockProvider,
    LockBody,
    LockingError,
)
from tfstate_git.utils.dependency_downloader import DependenciesManager
from tfstate_git.utils.sops_controller import Sops


@contextmanager
def assume_lock_conflict_on_error(lock_id: str):
    try:
        yield
    except Exception as e:
        raise LockingError(
            "Failed to lock state",
            lock_id=lock_id,
        ) from e


class StorageProvider(abc.ABC):
    @abc.abstractmethod
    def get_file(self, file_name: str): ...

    @abc.abstractmethod
    def put_file(self, file_name: str, data: str): ...

    @abc.abstractmethod
    def delete_file(self, file_name: str): ...

    @abc.abstractmethod
    def read_lock(self, file_name: str): ...

    @abc.abstractmethod
    def acquire_lock(self, file_name: str, data: LockBody): ...

    @abc.abstractmethod
    def release_lock(self, file_name: str): ...


class EncryptedStateLockProvider(BaseStateLockProvider):
    def __init__(
        self,
        manager: DependenciesManager,
        storage_driver: StorageProvider,
        state_file: str = "terraform.tfstate",
        key_path: pathlib.Path = "age_key.txt",
        sops_config_path: pathlib.Path = None,
    ):
        self.state_file = state_file
        self.storage_driver = storage_driver
        try:
            config = self.storage_driver.get_file(sops_config_path)

        except FileNotFoundError as e:
            raise FileNotFoundError("Sops config file not found cannot continue") from e

        self.sops = Sops(
            manager.get_dependency_location("sops"),
            config=config,
            env={
                "SOPS_AGE_KEY_FILE": str(key_path),
            },
        )

    async def get(self):
        data = self.storage_driver.get_file(self.state_file)
        if data is None:
            return None

        # decrypt data
        content = await self.sops.decrypt(self.state_file, data)
        return json.loads(content)

    async def put(self, lock_id: str, value: dict):
        await self._check_lock(lock_id)
        # lock is locked by me

        data = await self.sops.encrypt(str(self.state_file), json.dumps(value))
        self.storage_driver.put_file(self.state_file, data)

    async def delete(self, lock_id: str):
        await self._check_lock(lock_id)
        # lock is locked by me

        self.storage_driver.delete_file(self.state_file)

    async def _check_lock(self, lock_id: str):
        data = self.storage_driver.read_lock()
        if data is None:
            return None

        # decrypt data
        parsed = LockBody.model_validate_json(data)

        if parsed.ID != lock_id:
            raise LockingError(
                "Failed to lock state - someone else has already locked it",
                lock_id=lock_id,
            )

        return parsed

    def lock(self, data: LockBody):
        self.storage_driver.acquire_lock(self.state_file, data)

    def unlock(self):
        self.storage_driver.release_lock(self.state_file)
