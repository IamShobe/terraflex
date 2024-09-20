import os
import pathlib
from typing import Any, Self, override

from pydantic import BaseModel


from terraflex.server.storage_provider_base import (
    ItemKey,
    StorageProviderProtocol,
)
from terraflex.utils.dependency_manager import DependenciesManager


class EnvVarStorageProviderItemIdentifier(ItemKey):
    """Params required to reference an item in EnvVar storage provider.

    Attributes:
        key: The name of the environment variable to read.
    """

    key: str

    def as_string(self) -> str:
        return self.key


class EnvVarStorageProviderInitConfig(BaseModel):
    """Initialization params required to initialize EnvVar storage provider.

    EnvVar storage provider currently have no initialization params required.
    """


class EnvVarStorageProvider(StorageProviderProtocol):
    @override
    @classmethod
    async def from_config(
        cls,
        raw_config: Any,
        *,
        manager: DependenciesManager,
        workdir: pathlib.Path,
    ) -> Self:
        result = EnvVarStorageProviderInitConfig.model_validate(raw_config)
        return cls(
            **result.model_dump(),
        )

    @override
    @classmethod
    def validate_key(cls, key: dict) -> EnvVarStorageProviderItemIdentifier:
        return EnvVarStorageProviderItemIdentifier.model_validate(key)

    @override
    async def get_file(self, item_identifier: EnvVarStorageProviderItemIdentifier) -> bytes:
        if item_identifier.key not in os.environ:
            raise FileNotFoundError(f"Environment variable {item_identifier.key} not found")

        return os.environ[item_identifier.key].encode()
