from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, AsyncIterator
from fastapi import Depends, FastAPI, HTTPException, Query, Body, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import uvicorn
import yaml

from tfstate_git.server.config import ConfigFile, Settings
from tfstate_git.server.base_state_lock_provider import (
    StateLockProviderProtocol,
    Data,
    LockBody,
    LockingError,
)
from tfstate_git.server.storage_provider_base import (
    STORATE_PROVIDERS_ENTRYPOINT,
    AbstractStorageProvider,
)
from tfstate_git.server.tf_state_lock_controller import (
    TFStateLockController,
)
from tfstate_git.server.transformation_base import (
    TRANSFORMERS_ENTRYPOINT,
    AbstractTransformation,
)
from tfstate_git.utils.dependency_downloader import DependencyDownloader
from tfstate_git.utils.dependency_manager import DependenciesManager
from tfstate_git.utils.plugins import get_providers, get_providers_instances

config = Settings()  # type: ignore


READY_MESSAGE = """\
backend "http" {{
    address = "http://localhost:{port}/state"
    lock_address = "http://localhost:{port}/lock"
    lock_method = "PUT"
    unlock_address = "http://localhost:{port}/lock"
    unlock_method = "DELETE"
}}
"""


DEPENDENCIES_ENTRYPOINT = "tfformer.plugins.dependencies"


config_file_location = Path.cwd() / "examples" / "tfformer.yaml"
if config_file_location.exists():
    content = config_file_location.read_bytes()
    obj = yaml.safe_load(content)
    file_config = ConfigFile.model_validate(obj)


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
    storage_providers: dict[str, AbstractStorageProvider],
) -> list[AbstractTransformation]:
    transformer_providers = get_providers(
        AbstractTransformation,
        TRANSFORMERS_ENTRYPOINT,
    )

    transformers = []
    for transformer in config.transformers:
        if transformer.type not in transformer_providers:
            raise ValueError(f"Unsupported transformer type: {transformer.type}")

        transformer_class = transformer_providers[transformer.type].model_class
        transformers.append(
            await transformer_class.from_config(
                transformer.model_extra or {},
                storage_providers=storage_providers,
                manager=manager,
            )
        )

    return transformers


async def create_storage_providers(
    config: ConfigFile,
    manager: DependenciesManager,
) -> dict[str, AbstractStorageProvider]:
    storage_providers = get_providers(
        AbstractStorageProvider,
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
        )

    return result_storage_providers


async def initialize_controller() -> StateLockProviderProtocol:
    manager = await initialize_manager()

    storage_providers = await create_storage_providers(file_config, manager)
    transformers = await generate_transformers(file_config, manager, storage_providers)
    state_manager_storage = file_config.state_manager.storage
    state_storage_provider = storage_providers.get(state_manager_storage.provider)
    if state_storage_provider is None:
        raise ValueError(f"Undeclared storage provider: {state_manager_storage.provider}")

    state_key = state_storage_provider.validate_key(state_manager_storage.params or {})
    return TFStateLockController(
        storage_driver=state_storage_provider,
        data_transformers=transformers,
        state_file_storage_identifier=state_key,
    )


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


@app.get("/state")
async def get_state(controller: ControllerDependency) -> Data:
    # read the state file
    existing_state = await controller.get()
    if existing_state is None:
        raise HTTPException(status_code=404, detail="State not found")

    return existing_state


@app.post("/state")
async def update_state(
    lock_id: Annotated[str, Query(..., alias="ID", description="ID of the state to update")],
    new_state: Annotated[Any, Body(..., description="New state")],
    controller: ControllerDependency,
) -> None:
    return await controller.put(lock_id, new_state)


@app.delete("/state")
async def delete_state(controller: ControllerDependency) -> None:
    # TODO: should check if current user is holding the lock?
    lock = await controller.read_lock()
    if lock is None:
        raise HTTPException(status_code=404, detail="State not found")

    return await controller.delete(lock.ID)


@app.put("/lock")
def lock_state(body: LockBody, controller: ControllerDependency) -> None:
    return controller.lock(body)


@app.delete("/lock")
def unlock_state(controller: ControllerDependency) -> None:
    return controller.unlock()


def start_server(port: int) -> None:
    print("Add the following to your terraform configuration:")
    print(READY_MESSAGE.format(port=port))
    uvicorn.run(app, port=port)


if __name__ == "__main__":
    start_server(port=8600)
