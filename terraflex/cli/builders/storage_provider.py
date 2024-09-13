from typing import Optional
import questionary

from terraflex.cli.builders.git_storage import build_git_key_identifier, build_git_storage_provider
from terraflex.cli.builders.local_storage import build_local_key_identifier, build_local_storage_provider
from terraflex.server.config import (
    StorageProviderConfig,
    StorageProviderUsageConfig,
)


async def create_storage_provider_and_key(
    possible_providers,
    main_question: str,
    key_question: str,
    default_key_path: str,
    storage_provider_name: Optional[str] = None,
    local_storage_default_path: Optional[str] = None,
) -> tuple[str, StorageProviderConfig, StorageProviderUsageConfig]:
    # ask how to store the state
    answer = await questionary.select(
        main_question,
        choices=possible_providers,
    ).ask_async()

    match answer:
        case "Git":
            # ask for the location of the git repository
            if storage_provider_name is None:
                storage_provider_name = "git"

            storage_provider = await build_git_storage_provider()
            key_identifier = await build_git_key_identifier(
                storage_provider_name,
                path=default_key_path,
                question=key_question,
            )

        case "Local":
            if storage_provider_name is None:
                storage_provider_name = "local"

            storage_provider = await build_local_storage_provider(local_storage_default_path)
            key_identifier = await build_local_key_identifier(
                storage_provider_name,
                path=default_key_path,
                question=key_question,
            )

        case _:
            raise ValueError("Invalid selection")

    return storage_provider_name, storage_provider, key_identifier
