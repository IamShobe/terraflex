import pathlib
from typing import Any, Self, override

from pydantic import BaseModel

from tfstate_git.server.base_state_lock_provider import LockBody
from tfstate_git.server.storage_provider_base import (
    ItemKey,
    AbstractStorageProvider,
)
from tfstate_git.utils.dependency_manager import DependenciesManager


class LocalStorageProviderItemIdentifier(ItemKey):
    path: str

    def as_string(self) -> str:
        return self.path


class LocalStorageProviderInitConfig(BaseModel):
    folder: pathlib.Path


class LocalStorageProvider(AbstractStorageProvider):
    def __init__(self, folder: pathlib.Path) -> None:
        self.folder = folder.expanduser()

    @override
    @classmethod
    async def from_config(
        cls,
        raw_config: Any,
        *,
        manager: DependenciesManager,
        workdir: pathlib.Path,
    ) -> Self:
        result = LocalStorageProviderInitConfig.model_validate(raw_config)
        return cls(
            **result.model_dump(),
        )

    @override
    @classmethod
    def validate_key(cls, key: dict) -> LocalStorageProviderItemIdentifier:
        return LocalStorageProviderItemIdentifier.model_validate(key)

    @override
    def get_file(self, item_identifier: LocalStorageProviderItemIdentifier) -> bytes:
        file_name = item_identifier.path
        # read state
        state_file = self.folder / file_name
        try:
            return state_file.read_bytes()

        except FileNotFoundError as exc:
            raise FileNotFoundError(f"File {state_file} not found") from exc

    @override
    def put_file(self, item_identifier: LocalStorageProviderItemIdentifier, data: bytes) -> None:
        file_name = item_identifier.path
        # save state
        state_file = self.folder / file_name
        state_file.write_bytes(data)

    @override
    def delete_file(self, item_identifier: LocalStorageProviderItemIdentifier) -> None:
        file_name = item_identifier.path
        # delete state
        state_file = self.folder / file_name
        state_file.unlink()

    @override
    def read_lock(self, item_identifier: LocalStorageProviderItemIdentifier) -> bytes:
        file_name = item_identifier.path
        # read lock data
        lock_file = self.folder / "locks" / f"{file_name}.lock"
        if not lock_file.exists():
            raise FileNotFoundError(f"Lock file {lock_file} not found")

        return lock_file.read_bytes()

    @override
    def acquire_lock(self, item_identifier: LocalStorageProviderItemIdentifier, data: LockBody) -> None:
        file_name = item_identifier.path
        # make sure lock folder exists
        locks_dir = self.folder / "locks"
        locks_dir.mkdir(exist_ok=True)
        # write lock file
        lock_file = locks_dir / f"{file_name}.lock"
        lock_file.write_bytes(data.model_dump_json().encode())

    @override
    def release_lock(self, item_identifier: LocalStorageProviderItemIdentifier) -> None:
        file_name = item_identifier.path
        locks_dir = self.folder / "locks"
        lock_file = locks_dir / f"{file_name}.lock"
        lock_file.unlink()
