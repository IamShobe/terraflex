import pathlib
import subprocess
from typing import Any, Self, override

from pydantic import BaseModel


from terraflex.server.storage_provider_base import (
    ItemKey,
    StorageProviderProtocol,
)
from terraflex.utils.dependency_manager import DependenciesManager


class OnePasswordProviderItemIdentifier(ItemKey):
    """Params required to reference an item in 1Password storage provider.

    Attributes:
        reference_uri: 1Password URI to the item. Example: `op://<vault>/<item>/<field>`
    """

    reference_uri: str

    def as_string(self) -> str:
        return self.reference_uri.replace("/", "_").replace(":", "_")


class OnePasswordStorageProviderInitConfig(BaseModel):
    """Initialization params required to initialize 1Password storage provider.

    1Password storage provider currently have no initialization params required.
    """


class OnePasswordStorageProvider(StorageProviderProtocol):
    @override
    @classmethod
    async def from_config(
        cls,
        raw_config: Any,
        *,
        manager: DependenciesManager,
        workdir: pathlib.Path,
    ) -> Self:
        result = OnePasswordStorageProviderInitConfig.model_validate(raw_config)
        cls._validate_binary()
        return cls(
            **result.model_dump(),
        )

    @classmethod
    def _validate_binary(cls):
        try:
            subprocess.run(["op", "--version"], check=True, capture_output=True)
        except Exception as e:
            raise RuntimeError("1Password CLI not found in PATH") from e

    def _op(self, command: str, *args: str) -> str:
        proc = subprocess.run(
            ["op", command, *args],
            capture_output=True,
            text=True,
            check=False,
        )

        if proc.returncode != 0:
            raise RuntimeError(f"Error running op command: {proc.stderr}")

        return proc.stdout

    @override
    @classmethod
    def validate_key(cls, key: dict) -> OnePasswordProviderItemIdentifier:
        return OnePasswordProviderItemIdentifier.model_validate(key)

    @override
    async def get_file(self, item_identifier: OnePasswordProviderItemIdentifier) -> bytes:
        try:
            return self._op("read", item_identifier.reference_uri).encode()

        except Exception as e:
            raise RuntimeError(f"Secret {item_identifier.reference_uri} couldn't be fetched") from e
