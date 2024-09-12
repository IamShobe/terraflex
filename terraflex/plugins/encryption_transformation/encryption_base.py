import abc
from typing import Any, Self


from terraflex.server.storage_provider_base import AbstractStorageProvider
from terraflex.utils.dependency_manager import DependenciesManager


class AbstractEncryption(abc.ABC):
    @classmethod
    @abc.abstractmethod
    async def from_config(
        cls,
        raw_config: Any,
        *,
        storage_providers: dict[str, AbstractStorageProvider],
        manager: DependenciesManager,
    ) -> Self: ...

    @abc.abstractmethod
    async def encrypt(self, file_name: str, content: bytes) -> bytes: ...

    @abc.abstractmethod
    async def decrypt(self, file_name: str, content: bytes) -> bytes: ...
