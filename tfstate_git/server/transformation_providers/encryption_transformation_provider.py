from dataclasses import dataclass
import pathlib
from typing import Optional

from tfstate_git.server.storage_providers.base_storage_provider import StorageProvider
from tfstate_git.server.transformation_providers.base_transformation_provider import (
    TransformationProvider,
)
from tfstate_git.utils.dependency_downloader import DependenciesManager
from tfstate_git.utils.sops_controller import Sops


@dataclass
class EncryptionConfig:
    key_path: Optional[pathlib.Path] = None
    sops_config_path: Optional[pathlib.Path] = None


class EncryptionTransformationProvider(TransformationProvider):
    def __init__(
        self,
        manager: DependenciesManager,
        encryption_config: EncryptionConfig,
        storage_driver: StorageProvider,
    ):
        self.storage_driver = storage_driver

        self.sops = self._get_sops_controller(manager, encryption_config)

    def _get_sops_controller(
        self, manager: DependenciesManager, encryption_config: EncryptionConfig | None
    ):
        if encryption_config is None:
            encryption_config = EncryptionConfig()

        config: str
        if encryption_config.sops_config_path is not None:
            try:
                config = self.storage_driver.get_file(
                    str(encryption_config.sops_config_path),
                )

            except Exception as e:
                raise RuntimeError("Sops config file not found cannot continue") from e

        env = {}
        if encryption_config.key_path is not None:
            env["SOPS_AGE_KEY_FILE"] = str(encryption_config.key_path)

        return Sops(
            manager.get_dependency_location("sops"),
            config=config,
            env=env,
        )

    async def on_file_save(self, filename: str, content: str) -> str:
        return await self.sops.encrypt(filename, content)

    async def on_file_read(self, filename: str, content: str) -> str:
        return await self.sops.decrypt(filename, content)
