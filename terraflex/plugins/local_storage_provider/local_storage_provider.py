import pathlib
from typing import Any, Self, override

from pydantic import BaseModel
from terraflex.server.base_state_lock_provider import LockBody
from terraflex.server.storage_provider_base import (
    ItemKey,
    LockableStorageProviderProtocol,
    parse_item_key,
)
from terraflex.utils.dependency_manager import DependenciesManager


class LocalStorageProviderItemIdentifier(ItemKey):
    """Params required to reference an item in Local storage provider.

    Attributes:
        path: The path to a specific file relative to the directory root,
            folders are also allowed as part of the path.
    """

    path: str

    @override
    def as_string(self) -> str:
        return self.path


class LocalStorageProviderInitConfig(BaseModel):
    """Initialization params required to initialize Local storage provider.

    Attributes:
        folder: The path to the directory where the files will be stored.
        folder_mode: The mode to set on the folder. Default: 0o700.
        file_mode: The mode to set on the files. Default: 0o600.
    """

    folder: pathlib.Path
    folder_mode: int = 0o700
    file_mode: int = 0o600


class LocalStorageProvider(LockableStorageProviderProtocol):
    def __init__(self, folder: pathlib.Path, folder_mode: int, file_mode: int) -> None:
        self.folder = folder.expanduser()
        self.folder_mode = folder_mode
        self.file_mode = file_mode

        if not self.folder.exists():
            self.folder.mkdir(parents=True, exist_ok=True)
            self.folder.chmod(self.folder_mode)

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
    def validate_key(cls, key: dict[str, Any]) -> LocalStorageProviderItemIdentifier:
        return LocalStorageProviderItemIdentifier.model_validate(key)

    @override
    async def get_file(self, item_identifier: ItemKey) -> bytes:
        parsed_key = parse_item_key(item_identifier, LocalStorageProviderItemIdentifier)
        file_name = parsed_key.path
        # read state
        state_file = self.folder / file_name
        try:
            return state_file.read_bytes()

        except FileNotFoundError as exc:
            raise FileNotFoundError(f"File {state_file} not found") from exc

    @override
    async def put_file(self, item_identifier: ItemKey, data: bytes) -> None:
        parsed_key = parse_item_key(item_identifier, LocalStorageProviderItemIdentifier)
        file_name = parsed_key.path
        # save state
        state_file = self.folder / file_name
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_bytes(data)
        state_file.chmod(self.file_mode)

    @override
    async def delete_file(self, item_identifier: ItemKey) -> None:
        parsed_key = parse_item_key(item_identifier, LocalStorageProviderItemIdentifier)
        file_name = parsed_key.path
        # delete state
        state_file = self.folder / file_name
        state_file.unlink()

    @override
    async def read_lock(self, item_identifier: ItemKey) -> LockBody:
        parsed_key = parse_item_key(item_identifier, LocalStorageProviderItemIdentifier)
        file_name = parsed_key.path
        # read lock data
        lock_file = self.folder / "locks" / f"{file_name}.lock"
        if not lock_file.exists():
            raise FileNotFoundError(f"Lock file {lock_file} not found")

        return LockBody.model_validate_json(lock_file.read_bytes())

    @override
    async def acquire_lock(self, item_identifier: ItemKey, data: LockBody) -> None:
        parsed_key = parse_item_key(item_identifier, LocalStorageProviderItemIdentifier)
        file_name = parsed_key.path
        # make sure lock folder exists
        locks_dir = self.folder / "locks"
        # write lock file
        lock_file = locks_dir / f"{file_name}.lock"
        lock_file.parent.mkdir(exist_ok=True, parents=True)
        lock_file.write_bytes(data.model_dump_json().encode())

    @override
    async def release_lock(self, item_identifier: ItemKey) -> None:
        parsed_key = parse_item_key(item_identifier, LocalStorageProviderItemIdentifier)
        file_name = parsed_key.path
        locks_dir = self.folder / "locks"
        lock_file = locks_dir / f"{file_name}.lock"
        lock_file.unlink()
