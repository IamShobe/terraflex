from typing import Any, Self, override

from pydantic import BaseModel

from terraflex.plugins.encryption_transformation.age.controller import AgeController, AgeKeygenController
from terraflex.plugins.encryption_transformation.age.downloader import AgeDownloader
from terraflex.plugins.encryption_transformation.encryption_base import AbstractEncryption
from terraflex.server.config import StorageProviderUsageConfig
from terraflex.server.storage_provider_base import AbstractStorageProvider
from terraflex.utils.dependency_downloader import DependencyDownloader
from terraflex.utils.dependency_manager import DependenciesManager


class AgeKeyConfig(BaseModel):
    import_from_storage: StorageProviderUsageConfig


AgeDependency = DependencyDownloader(
    names=["age", "age-keygen"],
    version="1.2.0",
    downloader=AgeDownloader(),
)


class AgeEncryptionProvider(AbstractEncryption):
    TYPE = "age"

    def __init__(
        self,
        controller: AgeController,
    ):
        self.controller = controller

    @classmethod
    async def from_config(
        cls,
        raw_config: Any,
        *,
        storage_providers: dict[str, AbstractStorageProvider],
        manager: DependenciesManager,
    ) -> Self:
        config = AgeKeyConfig.model_validate(raw_config)
        storage_provider = storage_providers.get(config.import_from_storage.provider)
        if storage_provider is None:
            raise ValueError(f"Undeclared storage provider: {config.import_from_storage.provider}")

        storage_params = config.import_from_storage.params
        if storage_params is None:
            raise ValueError("Missing storage params")

        storage_key = storage_provider.validate_key(storage_params)
        private_key = storage_provider.get_file(storage_key)
        age_keygen_controller = AgeKeygenController(
            binary_location=manager.require_dependency("age-keygen"),
        )
        public_key = await age_keygen_controller.get_public_key_from_bytes(private_key)

        return cls(
            controller=AgeController(
                binary_location=manager.require_dependency("age"),
                private_key=private_key,
                public_key=public_key,
            )
        )

    @override
    async def encrypt(self, file_name: str, content: bytes) -> bytes:
        return await self.controller.encrypt(file_name, content)

    @override
    async def decrypt(self, file_name: str, content: bytes) -> bytes:
        return await self.controller.decrypt(file_name, content)
