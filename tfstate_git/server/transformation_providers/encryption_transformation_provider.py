from dataclasses import dataclass
import pathlib
from typing import Optional, Protocol

from tfstate_git.server.transformation_providers.transformation_protocol import (
    TransformationProtocol,
)


@dataclass
class EncryptionConfig:
    key_path: Optional[pathlib.Path] = None
    sops_config_path: Optional[pathlib.Path] = None


class EncryptionProtocol(Protocol):
    async def encrypt(self, file_name: str, content: bytes) -> bytes: ...
    async def decrypt(self, file_name: str, content: bytes) -> bytes: ...


class EncryptionTransformation(TransformationProtocol):
    def __init__(self, encryption_provider: EncryptionProtocol):
        self.encryption_provider = encryption_provider

    async def transform_read_file_content(self, filename: str, content: bytes) -> bytes:
        return await self.encryption_provider.decrypt(filename, content)

    async def transform_write_file_content(self, filename: str, content: bytes) -> bytes:
        return await self.encryption_provider.encrypt(filename, content)


# class EncryptionTransformationProvider(TransformationProtocol):
#     def __init__(
#         self,
#         manager: DependenciesManager,
#         encryption_config: EncryptionConfig,
#         storage_driver: StorageProviderProtocol,
#     ):
#         self.storage_driver = storage_driver

#         self.sops = self._get_sops_controller(manager, encryption_config)

#     def _get_sops_controller(
#         self, manager: DependenciesManager, encryption_config: EncryptionConfig | None
#     ) -> Sops:
#         if encryption_config is None:
#             encryption_config = EncryptionConfig()

#         config: str | None = None
#         if encryption_config.sops_config_path is not None:
#             path = encryption_config.sops_config_path
#             try:
#                 config = self.storage_driver.get_file(str(path))

#             except Exception as e:
#                 raise RuntimeError("Sops config file not found cannot continue") from e

#         env = {}
#         if encryption_config.key_path is not None:
#             env["SOPS_AGE_KEY_FILE"] = str(encryption_config.key_path)

#         return Sops(
#             manager.require_dependency("sops"),
#             config=config,
#             env=env,
#         )

#     @override
#     async def on_file_save(self, filename: str, content: str) -> str:
#         return await self.sops.encrypt(filename, content)

#     @override
#     async def on_file_read(self, filename: str, content: str) -> str:
#         return await self.sops.decrypt(filename, content)
