import questionary

from terraflex.cli.builders.git_storage import build_git_key_identifier
from terraflex.cli.builders.local_storage import build_local_key_identifier
from terraflex.cli.builders.storage_provider import create_storage_provider_and_key
from terraflex.plugins.encryption_transformation.age.controller import AgeKeygenController
from terraflex.server.app import (
    create_storage_providers,
    config as server_config,
)
from terraflex.server.config import (
    ConfigFile,
    StorageProviderUsageConfig,
    TransformerConfig,
)
from terraflex.plugins.encryption_transformation.encryption_transformation_provider import EncryptionTransformerConfig
from terraflex.plugins.encryption_transformation.age.provider import AgeKeyConfig
from terraflex.server.storage_provider_base import WriteableStorageProviderProtocol
from terraflex.utils.dependency_manager import DependenciesManager


async def generate_encryption_key(
    manager: DependenciesManager,
    config_file: ConfigFile,
    provider_name: str,
    key_identifier: StorageProviderUsageConfig,
) -> None:
    controller_location = manager.require_dependency("age-keygen")
    controller = AgeKeygenController(
        binary_location=controller_location,
    )
    private_key = await controller.generate_key_bytes()

    storage_providers = await create_storage_providers(
        config_file,
        manager,
        workdir=server_config.state_dir,
    )

    storage_provider_instance = storage_providers[provider_name]
    item_key = storage_provider_instance.validate_key(key_identifier.params or {})
    try:
        await storage_provider_instance.get_file(item_key)
        # file exists, ask if we should replace it
        should_replace = await questionary.confirm(
            "The key already exists, do you want to replace it?",
            default=False,
        ).ask_async()
        if not should_replace:
            print("Keeping existing key...")
            return

    except FileNotFoundError:
        pass

    if isinstance(storage_provider_instance, WriteableStorageProviderProtocol):
        await storage_provider_instance.put_file(item_key, private_key)


async def add_encryption_transformer(
    state_storage_provider_name: str, config_file: ConfigFile, manager: DependenciesManager
) -> str | None:
    transfomer_name = await questionary.text(
        "What is the name of the transformer?",
        default="encryption",
    ).ask_async()

    key_type = await questionary.select(
        "What type of key do you want to use for encryption?",
        choices=[
            "age",
        ],
    ).ask_async()

    match key_type:
        case "age":
            choices = [
                *[
                    questionary.Choice(f"{key} ({value.type})", value=(key, value))
                    for key, value in config_file.storage_providers.items()
                    if key != state_storage_provider_name
                ],
                questionary.Choice("Create a new storage", value="create"),
            ]

            selected_storage_provider = await questionary.select(
                "Where should the key be stored?",
                choices=choices,
            ).ask_async()

            if selected_storage_provider == "create":
                provider_name, storage_provider, key_identifier = await create_storage_provider_and_key(
                    possible_providers=["Local"],
                    main_question="How do you want to store the secret?",
                    key_question="What is the location of the secret key?",
                    default_key_path="age-key.txt",
                    storage_provider_name="encryption",
                    local_storage_default_path="~/secrets/",
                )

                config_file.storage_providers[provider_name] = storage_provider

            else:
                provider_name, storage_provider_config = selected_storage_provider
                # get a new key for the storage provider
                match storage_provider_config.type:
                    case "local":
                        key_identifier = await build_local_key_identifier(provider_name, path="age-key.txt")

                    case "git":
                        key_identifier = await build_git_key_identifier(provider_name, path="age-key.txt")

                    case _:
                        raise ValueError("Invalid selection")

            should_generate_key = await questionary.confirm(
                "Do you want to generate a new key?",
                default=True,
            ).ask_async()
            if should_generate_key:
                await generate_encryption_key(manager, config_file, provider_name, key_identifier)

            encryption_config = EncryptionTransformerConfig(
                key_type="age",
                **AgeKeyConfig(
                    import_from_storage=key_identifier,
                ).model_dump(),
            )

        case _:
            raise ValueError("Invalid selection")

    transformer_config = TransformerConfig(
        type="encryption",
        **encryption_config.model_dump(),
    )

    config_file.transformers[transfomer_name] = transformer_config

    return transfomer_name
