import asyncio
from contextlib import contextmanager
import multiprocessing
import subprocess
import pathlib
import time
from typing import Annotated, Iterator, Optional
import httpx
import typer
from uvicorn import Config, Server
import yaml
import questionary

from terraflex.plugins.encryption_transformation.age.controller import AgeKeygenController
from terraflex.server.app import (
    CONFIG_FILE_NAME,
    READY_MESSAGE,
    create_storage_providers,
    initialize_manager,
    start_server,
    app as server_app,
    config as server_config,
)
from terraflex.server.config import (
    ConfigFile,
    StateManagerConfig,
    StorageProviderConfig,
    StorageProviderUsageConfig,
    TransformerConfig,
)
from terraflex.plugins.git_storage_provider.git_storage_provider import (
    GitStorageProviderInitConfig,
    GitStorageProviderItemIdentifier,
)
from terraflex.plugins.local_storage_provider.local_storage_provider import (
    LocalStorageProviderInitConfig,
    LocalStorageProviderItemIdentifier,
)

from terraflex.plugins.encryption_transformation.encryption_transformation_provider import EncryptionTransformerConfig
from terraflex.plugins.encryption_transformation.age.provider import AgeKeyConfig
from terraflex.utils.dependency_manager import DependenciesManager


app = typer.Typer(pretty_exceptions_enable=False)


@contextmanager
def capture_aborts() -> Iterator[None]:
    try:
        yield
    except typer.Abort as e:
        print("Error:", e)
        raise


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
    provider_name, path, question="What is the location of the file?"
) -> StorageProviderUsageConfig:
    path = await questionary.text(
        question,
        default=path,
    ).ask_async()

    return StorageProviderUsageConfig(
        provider=provider_name,
        params=LocalStorageProviderItemIdentifier(path=path).model_dump(),
    )


async def add_encryption_transformer(
    state_storage_provider_name: str, config_file: ConfigFile, manager: DependenciesManager
) -> None:
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
                storage_provider_instance.get_file(item_key)
                # file exists, ask if we should replace it
                should_replace = await questionary.confirm(
                    "The key already exists, do you want to replace it?",
                    default=False,
                ).ask_async()
                if not should_replace:
                    print("Aborting...")
                    return

            except FileNotFoundError:
                pass

            storage_provider_instance.put_file(item_key, private_key)

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
    config_file.transformers.append(transformer_config)


async def create_storage_provider_and_key(
    possible_providers,
    main_question: str,
    key_question: str,
    default_key_path: str,
    storage_provider_name: Optional[str] = None,
    local_storage_default_path: Optional[str] = None,
):
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


async def wizard(manager: DependenciesManager) -> ConfigFile:
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


async def _init() -> None:
    manager = await initialize_manager()
    config_file_location = pathlib.Path(CONFIG_FILE_NAME)
    if config_file_location.exists():
        print("Configuration file already exists")
        should_replace = await questionary.confirm(
            "Do you want to replace it?",
            default=False,
        ).ask_async()
        if not should_replace:
            print("Aborting...")
            return

        print("Replacing existing configuration file")

    result_file = await wizard(manager)
    raw_file = yaml.safe_dump(yaml.safe_load(result_file.model_dump_json()))
    config_file_location.write_text(raw_file, encoding="utf-8")

    print("\n\n")
    print("Configuration file created")
    print("You can now start the server with `terraflex start`")
    print("In terraform backend configuration, use the following:\n")
    print(READY_MESSAGE.format(port=8600))


@app.command()
def init() -> None:
    with capture_aborts():
        asyncio.run(_init())


@app.command()
def start(
    port: Annotated[int, typer.Option(help="Port to run the server on")] = 8600,
) -> None:
    start_server(port)


class UvicornServer(multiprocessing.Process):
    def __init__(self, config: Config):
        super().__init__()
        self.server = Server(config=config)
        self.config = config

    def stop(self):
        self.terminate()

    def run(self, *args, **kwargs):
        self.server.run()


def wait_until_ready(port: int):
    client = httpx.Client()
    while True:
        try:
            response = client.get(f"http://localhost:{port}/ready")
            response.raise_for_status()
            break
        except Exception:
            time.sleep(0.2)


@app.command()
def wrap(
    verbose: Annotated[
        bool,
        typer.Option("-v", "--verbose", help="Print more details about the backend"),
    ] = False,
    port: Annotated[int, typer.Option(help="Port to run the server on")] = 8600,
    args: list[str] = typer.Argument(help="Command to run"),
) -> None:
    instance = UvicornServer(
        config=Config(
            app=server_app,
            port=port,
            access_log=verbose,
            log_level="info" if verbose else "warning",
        )
    )
    instance.start()
    wait_until_ready(port)
    # run the command
    subprocess.run(args)
    instance.stop()


def main() -> None:
    app()
