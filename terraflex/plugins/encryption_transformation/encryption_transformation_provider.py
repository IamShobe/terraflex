import pathlib
from typing import Any, Self, override

from pydantic import BaseModel, ConfigDict
from terraflex.plugins.encryption_transformation.encryption_base import EncryptionProtocol
from terraflex.server.storage_provider_base import StorageProviderProtocol
from terraflex.server.transformation_base import (
    TransformerProtocol,
)
from terraflex.utils.dependency_manager import DependenciesManager
from terraflex.utils.plugins import get_providers

ENCRYPTION_PROVIDER_ENTRYPOINT = "terraflex.plugins.transformer.encryption"


class EncryptionTransformerConfig(BaseModel):
    """Transformer that encrypts and decrypts the content of the files using the specified encryption provider.

    Attributes:
        key_type: The type of the encryption key.
        **kwargs: Additional configuration for the encryption provider.

    Example:
        Encryption transformer with `age` encryption provider:
        ```yaml
        type: encryption
        key_type: age
        import_from_storage:
            provider: envvar
            params:
                key: AGE_PRIVATE_KEY
        ```
    """

    model_config = ConfigDict(extra="allow")
    key_type: str


encryption_providers = get_providers(EncryptionProtocol, ENCRYPTION_PROVIDER_ENTRYPOINT)


class EncryptionTransformation(TransformerProtocol):
    def __init__(self, encryption_provider: EncryptionProtocol):
        self.encryption_provider = encryption_provider

    @override
    @classmethod
    async def from_config(
        cls,
        raw_config: Any,
        *,
        storage_providers: dict[str, StorageProviderProtocol],
        manager: DependenciesManager,
        workdir: pathlib.Path,
    ) -> Self:
        config = EncryptionTransformerConfig.model_validate(raw_config)
        encryption_provider = encryption_providers.get(config.key_type)
        if encryption_provider is None:
            raise ValueError(f"Unsupported encryption key type: {config.key_type}")

        encryption_controller_class = encryption_provider.model_class
        controller = await encryption_controller_class.from_config(
            raw_config,
            storage_providers=storage_providers,
            manager=manager,
        )

        return cls(encryption_provider=controller)

    @override
    async def transform_read_file_content(self, file_identifier: str, content: bytes) -> bytes:
        return await self.encryption_provider.decrypt(file_identifier, content)

    @override
    async def transform_write_file_content(self, file_identifier: str, content: bytes) -> bytes:
        return await self.encryption_provider.encrypt(file_identifier, content)
