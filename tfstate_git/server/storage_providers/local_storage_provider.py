import pathlib

from tfstate_git.server.base_state_lock_provider import LockBody
from tfstate_git.server.encrypted_storage_state_lock_provider import (
    StorageProvider,
)


class LocalStorageProvider(StorageProvider):
    def __init__(self, folder: pathlib.Path) -> None:
        self.folder = pathlib.Path(folder)

    def get_file(self, file_name: str):
        # read state
        state_file = self.folder / file_name
        try:
            return state_file.read_text()

        except FileNotFoundError:
            return None

    def put_file(self, file_name: str, data: str):
        # save state
        state_file = self.folder / file_name
        state_file.write_text(data)

    def delete_file(self, file_name: str):
        # delete state
        state_file = self.folder / file_name
        state_file.unlink()

    def read_lock(self, file_name: str):
        # read lock data
        lock_file = self.folder / "locks" / f"{file_name}.lock"
        if not lock_file.exists():
            return None

        return lock_file.read_bytes()

    def acquire_lock(self, file_name: str, data: LockBody):
        # make sure lock folder exists
        locks_dir = self.folder / "locks"
        locks_dir.mkdir(exist_ok=True)
        # write lock file
        lock_file = locks_dir / f"{file_name}.lock"
        lock_file.write_bytes(data.model_dump_json().encode())

    def release_lock(self, file_name: str):
        locks_dir = self.folder / "locks"
        lock_file = locks_dir / f"{file_name}.lock"
        lock_file.unlink()
