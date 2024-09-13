import questionary

from terraflex.cli.builders.encryption_transformer import add_encryption_transformer
from terraflex.cli.builders.storage_provider import create_storage_provider_and_key
from terraflex.server.config import (
    ConfigFile,
    StackConfig,
)

from terraflex.utils.dependency_manager import DependenciesManager


async def start_configfile_creation_wizard(manager: DependenciesManager) -> tuple[str, ConfigFile]:
    # ask for the name of the stack
    stack_name = await questionary.text(
        "What is the name of the stack?",
        default="main",
    ).ask_async()
    if not stack_name:
        raise ValueError("Invalid stack name")

    # ask how to store the state
    storage_provider_name, storage_provider, key_identifier = await create_storage_provider_and_key(
        possible_providers=["Git", "Local"],
        main_question="How do you want to store the terraform state?",
        key_question="What is the location of the state file?",
        default_key_path="terraform.tfstate",
    )

    stack_config = StackConfig(
        state_storage=key_identifier,
        transformers=[],
    )

    result_file = ConfigFile(
        version="2",
        storage_providers={
            storage_provider_name: storage_provider,
        },
        transformers={},
        stacks={
            stack_name: stack_config,
        },
    )

    # ask if the user wants to add encryption
    should_add_encryption = await questionary.confirm(
        "Do you want to add encryption to the state?",
        default=True,
    ).ask_async()
    if should_add_encryption:
        encryption_name = await add_encryption_transformer(storage_provider_name, result_file, manager)
        if encryption_name is not None:
            stack_config.transformers.append(encryption_name)

    return stack_name, result_file
