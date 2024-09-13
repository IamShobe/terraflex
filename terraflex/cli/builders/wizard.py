import questionary

from terraflex.cli.builders.encryption_transformer import add_encryption_transformer
from terraflex.cli.builders.storage_provider import create_storage_provider_and_key
from terraflex.server.config import (
    ConfigFile,
    StateManagerConfig,
)

from terraflex.utils.dependency_manager import DependenciesManager


async def start_configfile_creation_wizard(manager: DependenciesManager) -> ConfigFile:
    # ask how to store the state
    storage_provider_name, storage_provider, key_identifier = await create_storage_provider_and_key(
        possible_providers=["Git", "Local"],
        main_question="How do you want to store the terraform state?",
        key_question="What is the location of the state file?",
        default_key_path="terraform.tfstate",
    )

    result_file = ConfigFile(
        version="1",
        storage_providers={
            storage_provider_name: storage_provider,
        },
        transformers=[],
        state_manager=StateManagerConfig(
            storage=key_identifier,
        ),
    )

    # ask if the user wants to add encryption
    should_add_encryption = await questionary.confirm(
        "Do you want to add encryption to the state?",
        default=True,
    ).ask_async()
    if should_add_encryption:
        await add_encryption_transformer(storage_provider_name, result_file, manager)

    return result_file
