

import abc

from tfstate_git.server.base_state_lock_provider import LockBody


class StorageProvider(abc.ABC):
    @abc.abstractmethod
    def get_file(self, file_name: str) -> str | None: ...

    @abc.abstractmethod
    def put_file(self, file_name: str, data: str) -> None: ...

    @abc.abstractmethod
    def delete_file(self, file_name: str) -> None: ...

    @abc.abstractmethod
    def read_lock(self, file_name: str) -> bytes | None: ...

    @abc.abstractmethod
    def acquire_lock(self, file_name: str, data: LockBody) -> None: ...

    @abc.abstractmethod
    def release_lock(self, file_name: str) -> None: ...
