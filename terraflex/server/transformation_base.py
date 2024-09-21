import pathlib
from typing import Any, Protocol, Self, runtime_checkable

from terraflex.server.storage_provider_base import StorageProviderProtocol
from terraflex.utils.dependency_manager import DependenciesManager

TRANSFORMERS_ENTRYPOINT = "terraflex.plugins.transformer"


@runtime_checkable
class TransformerProtocol(Protocol):
    """Protocol for state transformation providers.

    Every state transformation provider must implement `TransformerProtocol` methods - and register to the `terraflex.plugins.transformer` entrypoint.

    Example:
        Register encryption transformer - if your project is based on poetry:
        ```toml
        [tool.poetry.plugins."terraflex.plugins.transformer"]
        encryption = "terraflex.plugins.encryption_transformation.encryption_transformation_provider:EncryptionTransformation"
        ```
    """

    @classmethod
    async def from_config(
        cls,
        raw_config: Any,
        *,
        storage_providers: dict[str, StorageProviderProtocol],
        manager: DependenciesManager,
        workdir: pathlib.Path,
    ) -> Self:
        """Create an instance of the transformation provider from the configuration.

        Args:
            raw_config: The raw configuration propagated from the transformer config.
            storage_providers: All the initialized storage providers specified in the config file.
            manager: The dependencies manager - allows to request a binary path from.
            workdir: The data directory of terraflex - located at `~/.local/share/terraflex` -
                can be used to manage state of the provider.
        """
        ...

    async def transform_write_file_content(self, file_identifier: str, content: bytes) -> bytes:
        """Transform the content of the file before writing it to the storage provider.

        Args:
            file_identifier: The identifier of the file - calculated by calling to_string()
                method of the storage usage params.
            content: The content of the file.
        """
        ...

    async def transform_read_file_content(self, file_identifier: str, content: bytes) -> bytes:
        """Transform the content of the file after reading it from the storage provider.

        Args:
            file_identifier: The identifier of the file - calculated by calling to_string()
                method of the storage usage params.
            content: The content of the file.
        """
        ...
