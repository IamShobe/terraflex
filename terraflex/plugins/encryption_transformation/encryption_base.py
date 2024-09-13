from typing import Any, Protocol, Self, runtime_checkable


from terraflex.server.storage_provider_base import StorageProviderProtocol
from terraflex.utils.dependency_manager import DependenciesManager


@runtime_checkable
class EncryptionProtocol(Protocol):
    @classmethod
    async def from_config(
        cls,
        raw_config: Any,
        *,
        storage_providers: dict[str, StorageProviderProtocol],
        manager: DependenciesManager,
    ) -> Self: ...

    async def encrypt(self, file_name: str, content: bytes) -> bytes: ...
    async def decrypt(self, file_name: str, content: bytes) -> bytes: ...
