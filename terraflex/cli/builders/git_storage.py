import questionary

from terraflex.server.config import (
    StorageProviderConfig,
    StorageProviderUsageConfig,
)

from terraflex.plugins.git_storage_provider.git_storage_provider import (
    GitStorageProviderInitConfig,
    GitStorageProviderItemIdentifier,
)


async def build_git_storage_provider() -> StorageProviderConfig:
    origin_url = await questionary.path(
        "What is the origin url?",
    ).ask_async()

    return StorageProviderConfig(
        type="git",
        **GitStorageProviderInitConfig(origin_url=origin_url).model_dump(),
    )


async def build_git_key_identifier(
    provider_name, path, question="What is the location of the file?"
) -> StorageProviderUsageConfig:
    path = await questionary.text(
        question,
        default=path,
    ).ask_async()

    return StorageProviderUsageConfig(
        provider=provider_name,
        params=GitStorageProviderItemIdentifier(path=path).model_dump(),
    )
