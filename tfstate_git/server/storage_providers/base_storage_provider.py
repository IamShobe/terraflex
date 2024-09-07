

import abc

from tfstate_git.server.base_state_lock_provider import LockBody


class StorageProvider(abc.ABC):
    @abc.abstractmethod
    def get_file(self, file_name: str) -> str: ...

    @abc.abstractmethod
    def put_file(self, file_name: str, data: str): ...

    @abc.abstractmethod
    def delete_file(self, file_name: str): ...

    @abc.abstractmethod
    def read_lock(self, file_name: str) -> str: ...

    @abc.abstractmethod
    def acquire_lock(self, file_name: str, data: LockBody): ...

    @abc.abstractmethod
    def release_lock(self, file_name: str): ...
