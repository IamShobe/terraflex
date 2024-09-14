import os
import pathlib
from typing import Any, Optional, Self, override

from onepassword import Client
from pydantic import BaseModel


from terraflex.server.storage_provider_base import (
    ItemKey,
    StorageProviderProtocol,
)
from terraflex.utils.dependency_manager import DependenciesManager


class OnePasswordProviderItemIdentifier(ItemKey):
    reference_uri: str

    def as_string(self) -> str:
        return self.reference_uri


class OnePasswordStorageProviderInitConfig(BaseModel):
    token: Optional[str] = None


class OnePasswordStorageProvider(StorageProviderProtocol):
    def __init__(self, client: Client) -> None:
        self.client = client

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
        result.token = result.token or os.getenv("OP_SERVICE_ACCOUNT_TOKEN")
        client = await Client.authenticate(
            auth=result.token, integration_name="Terraflex", integration_version="v0.1.0"
        )
        return cls(
            client=client,
        )

    @override
    @classmethod
    def validate_key(cls, key: dict) -> OnePasswordProviderItemIdentifier:
        return OnePasswordProviderItemIdentifier.model_validate(key)

    @override
    async def get_file(self, item_identifier: OnePasswordProviderItemIdentifier) -> bytes:
        try:
            return (await self.client.secrets.resolve(item_identifier.reference_uri)).encode()

        except Exception as e:
            raise RuntimeError(f"Secret {item_identifier.reference_uri} couldn't be fetched") from e
