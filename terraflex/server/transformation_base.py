import pathlib
from typing import Any, Protocol, Self, runtime_checkable

from terraflex.server.storage_provider_base import StorageProviderProtocol
from terraflex.utils.dependency_manager import DependenciesManager


TRANSFORMERS_ENTRYPOINT = "terraflex.plugins.transformer"


@runtime_checkable
class TransformerProtocol(Protocol):
    @classmethod
    async def from_config(
        cls,
        raw_config: Any,
        *,
        storage_providers: dict[str, StorageProviderProtocol],
        manager: DependenciesManager,
        workdir: pathlib.Path,
    ) -> Self: ...

    async def transform_write_file_content(self, file_identifier: str, content: bytes) -> bytes: ...
    async def transform_read_file_content(self, file_identifier: str, content: bytes) -> bytes: ...


if __name__ == "__main__":
    print("hey")
