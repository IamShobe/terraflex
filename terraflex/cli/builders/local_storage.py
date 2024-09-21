import pathlib
from typing import Optional

import questionary

from terraflex.plugins.local_storage_provider.local_storage_provider import (
    LocalStorageProviderInitConfig,
    LocalStorageProviderItemIdentifier,
)
from terraflex.server.config import (
    StorageProviderConfig,
    StorageProviderUsageConfig,
)


async def build_local_storage_provider(local_storage_default_path: Optional[str] = None) -> StorageProviderConfig:
    folder = pathlib.Path(
        await questionary.path(
            "Where is the folder located?",
            default=local_storage_default_path or "",
        ).ask_async()
    )

    return StorageProviderConfig(
        type="local",
        **LocalStorageProviderInitConfig(folder=folder).model_dump(),
    )


async def build_local_key_identifier(
    provider_name: str, path: str, question: str = "What is the location of the file?"
) -> StorageProviderUsageConfig:
    path = await questionary.text(
        question,
        default=path,
    ).ask_async()

    return StorageProviderUsageConfig(
        provider=provider_name,
        params=LocalStorageProviderItemIdentifier(path=path).model_dump(),
    )
