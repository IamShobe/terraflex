from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, AsyncIterator, Literal
from fastapi import Depends, FastAPI, HTTPException, Query, Body, Request, status, Path as PathDep
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import uvicorn
import yaml

from terraflex.server.config import ConfigFile, Settings
from terraflex.server.base_state_lock_provider import (
    StateLockProviderProtocol,
    Data,
    LockBody,
    LockingError,
)
from terraflex.server.storage_provider_base import (
    STORATE_PROVIDERS_ENTRYPOINT,
    StorageProviderProtocol,
    WriteableStorageProviderProtocol,
)
from terraflex.server.tf_state_lock_controller import (
    TFStack,
    TFStateLockController,
)
from terraflex.server.transformation_base import (
    TRANSFORMERS_ENTRYPOINT,
    TransformerProtocol,
)
from terraflex.utils.dependency_downloader import DependencyDownloader
from terraflex.utils.dependency_manager import DependenciesManager
from terraflex.utils.plugins import get_providers, get_providers_instances

config = Settings()  # type: ignore


DEPENDENCIES_ENTRYPOINT = "terraflex.plugins.dependencies"

CONFIG_FILE_NAME = "terraflex.yaml"


async def initialize_manager() -> DependenciesManager:
    dependencies_providers = get_providers_instances(
        DependencyDownloader,
        DEPENDENCIES_ENTRYPOINT,
    )

    manager = DependenciesManager(
        dependencies=[downloader.instance for downloader in dependencies_providers.values()],
        dest_folder=config.state_dir,
    )
    await manager.initialize()
    return manager


async def generate_transformers(
    config: ConfigFile,
    manager: DependenciesManager,
    storage_providers: dict[str, StorageProviderProtocol],
    workdir: Path,
) -> dict[str, TransformerProtocol]:
    transformer_providers = get_providers(
        TransformerProtocol,
        TRANSFORMERS_ENTRYPOINT,
    )

    transformers: dict[str, TransformerProtocol] = {}
    for name, transformer in config.transformers.items():
        if transformer.type not in transformer_providers:
            raise ValueError(f"Unsupported transformer type: {transformer.type}")

        transformer_class = transformer_providers[transformer.type].model_class
        transformers[name] = await transformer_class.from_config(
            transformer.model_extra or {},
            storage_providers=storage_providers,
            manager=manager,
            workdir=workdir,
        )

    return transformers


async def create_storage_providers(
    config: ConfigFile,
    manager: DependenciesManager,
    workdir: Path,
) -> dict[str, StorageProviderProtocol]:
    storage_providers = get_providers(
        StorageProviderProtocol,
        STORATE_PROVIDERS_ENTRYPOINT,
    )

    result_storage_providers = {}
    for name, storage_config in config.storage_providers.items():
        if storage_config.type not in storage_providers:
            raise ValueError(f"Unsupported storage provider type: {storage_config.type}")

        storage_class = storage_providers[storage_config.type].model_class
        result_storage_providers[name] = await storage_class.from_config(
            storage_config.model_extra or {},
            manager=manager,
            workdir=workdir,
        )

    return result_storage_providers


async def generate_stacks(
    config: ConfigFile,
    storage_providers: dict[str, StorageProviderProtocol],
    transformers: dict[str, TransformerProtocol],
) -> dict[str, TFStack]:
    result: dict[str, TFStack] = {}

    for stack_name, stack in config.stacks.items():
        state_storage_provider = storage_providers.get(stack.state_storage.provider)
        if state_storage_provider is None:
            raise ValueError(f"Undeclared storage provider: {stack.state_storage.provider}")

        stack_transformers: list[TransformerProtocol] = []
        for transformer_name in stack.transformers:
            transformer = transformers.get(transformer_name)
            if transformer is None:
                raise ValueError(f"Undeclared transformer: {transformer_name}")

            stack_transformers.append(transformer)

        state_key = state_storage_provider.validate_key(stack.state_storage.params or {})
        if not isinstance(state_storage_provider, WriteableStorageProviderProtocol):
            raise ValueError(
                f"Storage provider {stack.state_storage.provider} does not support writing - and it's required for state management"
            )

        result[stack_name] = TFStack(
            name=stack_name,
            storage_driver=state_storage_provider,
            data_transformers=stack_transformers,
            state_file_storage_identifier=state_key,
        )

    return result


async def initialize_controller() -> StateLockProviderProtocol:
    config_file_location = Path.cwd() / CONFIG_FILE_NAME
    if not config_file_location.exists():
        raise FileNotFoundError(f"Config file not found: {config_file_location}")

    content = config_file_location.read_bytes()
    obj = yaml.safe_load(content)
    file_config = ConfigFile.model_validate(obj)

    manager = await initialize_manager()

    storage_providers = await create_storage_providers(file_config, manager, workdir=config.state_dir)
    transformers = await generate_transformers(file_config, manager, storage_providers, workdir=config.state_dir)
    stacks = await generate_stacks(file_config, storage_providers, transformers)

    return TFStateLockController(stacks=stacks)


state = {}


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    state["controller"] = await initialize_controller()
    yield


def get_controller() -> StateLockProviderProtocol:
    return state["controller"]


ControllerDependency = Annotated[StateLockProviderProtocol, Depends(get_controller)]

app = FastAPI(lifespan=lifespan)


@app.exception_handler(LockingError)
async def validation_exception_handler(_: Request, exc: LockingError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=jsonable_encoder({"detail": str(exc), "ID": exc.lock_id}),
    )


@app.get("/{stack_name}/state")
async def get_state(stack_name: str, controller: ControllerDependency) -> Data:
    # read the state file
    existing_state = await controller.get(stack_name)
    if existing_state is None:
        raise HTTPException(status_code=404, detail="State not found")

    return existing_state


@app.post("/{stack_name}/state")
async def update_state(
    stack_name: str,
    lock_id: Annotated[str, Query(..., alias="ID", description="ID of the state to update")],
    new_state: Annotated[Any, Body(..., description="New state")],
    controller: ControllerDependency,
) -> None:
    return await controller.put(stack_name, lock_id, new_state)


@app.delete("/{stack_name}/state")
async def delete_state(stack_name: str, controller: ControllerDependency) -> None:
    # TODO: should check if current user is holding the lock?
    lock = await controller.read_lock(stack_name)
    if lock is None:
        raise HTTPException(status_code=404, detail="State not found")

    return await controller.delete(stack_name, lock.ID)


@app.put("/{stack_name}/lock")
def lock_state(stack_name: Annotated[str, PathDep()], body: LockBody, controller: ControllerDependency) -> None:
    return controller.lock(stack_name, body)


@app.delete("/{stack_name}/lock")
def unlock_state(stack_name: str, controller: ControllerDependency) -> None:
    return controller.unlock(stack_name)


@app.get("/ready")
def ready() -> Literal["Ready"]:
    return "Ready"


def start_server(port: int) -> None:
    uvicorn.run(app, port=port)


if __name__ == "__main__":
    start_server(port=8600)
