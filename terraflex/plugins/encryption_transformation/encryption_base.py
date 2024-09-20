from typing import Any, Protocol, Self, runtime_checkable


from terraflex.server.storage_provider_base import StorageProviderProtocol
from terraflex.utils.dependency_manager import DependenciesManager


@runtime_checkable
class EncryptionProtocol(Protocol):
    """Protocol for encryption providers.


    Every encryption provider must implement `EncryptionProtocol` methods - and register to the `terraflex.plugins.transformer.encryption` entrypoint.

    Example:
        Register age encryption provider - if your project is based on poetry:
        ```toml
        [tool.poetry.plugins."terraflex.plugins.transformer.encryption"]
        age = "terraflex.plugins.encryption_transformation.age.provider:AgeEncryptionProvider"
        ```
    """

    @classmethod
    async def from_config(
        cls,
        raw_config: Any,
        *,
        storage_providers: dict[str, StorageProviderProtocol],
        manager: DependenciesManager,
    ) -> Self:
        """Create an instance of the encryption provider from the configuration.

        Args:
            raw_config: The raw configuration propagated from the transformer config.
            storage_providers: All the initialized storage providers specified in the config file.
            manager: The dependencies manager - allows to request a binary path from.

        Returns:
            The initialized instance of the encryption provider.
        """
        ...

    async def encrypt(self, file_name: str, content: bytes) -> bytes:
        """Encrypt the content of the file.

        Args:
            file_name: The name of the file.
            content: The content of the file.

        Returns:
            The encrypted content.
        """
        ...

    async def decrypt(self, file_name: str, content: bytes) -> bytes:
        """Decrypt the content of the file.

        Args:
            file_name: The name of the file.
            content: The content of the file.

        Returns:
            The decrypted content.
        """
        ...
