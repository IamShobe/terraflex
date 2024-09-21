import os
import pathlib
from typing import Any, Self, override

from pydantic import BaseModel
from terraflex.server.storage_provider_base import (
    ItemKey,
    StorageProviderProtocol,
    parse_item_key,
)
from terraflex.utils.dependency_manager import DependenciesManager


class EnvVarStorageProviderItemIdentifier(ItemKey):
    """Params required to reference an item in EnvVar storage provider.

    Attributes:
        key: The name of the environment variable to read.
    """

    key: str

    @override
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
    def validate_key(cls, key: dict[str, Any]) -> EnvVarStorageProviderItemIdentifier:
        return EnvVarStorageProviderItemIdentifier.model_validate(key)

    @override
    async def get_file(self, item_identifier: ItemKey) -> bytes:
        parsed_key = parse_item_key(item_identifier, EnvVarStorageProviderItemIdentifier)
        if parsed_key.key not in os.environ:
            raise FileNotFoundError(f"Environment variable {parsed_key.key} not found")

        return os.environ[parsed_key.key].encode()
