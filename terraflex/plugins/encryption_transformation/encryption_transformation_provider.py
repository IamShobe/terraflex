from dataclasses import dataclass
import pathlib
from typing import Any, Optional, Self, override

from pydantic import BaseModel, ConfigDict

from terraflex.plugins.encryption_transformation.encryption_base import AbstractEncryption
from terraflex.server.storage_provider_base import AbstractStorageProvider
from terraflex.server.transformation_base import (
    AbstractTransformation,
)
from terraflex.utils.dependency_manager import DependenciesManager
from terraflex.utils.plugins import get_providers

ENCRYPTION_PROVIDER_ENTRYPOINT = "terraflex.plugins.transformer.encryption"


@dataclass
class EncryptionConfig:
    key_path: Optional[pathlib.Path] = None
    sops_config_path: Optional[pathlib.Path] = None


class EncryptionTransformerConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    key_type: str


encryption_providers = get_providers(AbstractEncryption, ENCRYPTION_PROVIDER_ENTRYPOINT)


class EncryptionTransformation(AbstractTransformation):
    TYPE = "encryption"

    def __init__(self, encryption_provider: AbstractEncryption):
        self.encryption_provider = encryption_provider

    @override
    @classmethod
    async def from_config(
        cls,
        raw_config: Any,
        *,
        storage_providers: dict[str, AbstractStorageProvider],
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
