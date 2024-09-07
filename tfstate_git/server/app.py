from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, AsyncIterator
from fastapi import Depends, FastAPI, HTTPException, Query, Body, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import uvicorn
import yaml

from tfstate_git.server.adapters.age_controller import AgeController
from tfstate_git.server.config import ConfigFile, EncryptionTransformerConfig, Settings, StorageProviderConfig
from tfstate_git.server.base_state_lock_provider import (
    StateLockProviderProtocol,
    Data,
    LockBody,
    LockingError,
)
from tfstate_git.server.storage_providers.local_storage_provider import LocalStorageProvider
from tfstate_git.server.storage_providers.storage_provider_protocol import StorageProviderProtocol
from tfstate_git.server.tf_state_lock_controller import (
    TFStateLockController,
)
from tfstate_git.server.storage_providers.git_storage_provider import GitStorageProvider
from tfstate_git.server.transformation_providers.encryption_transformation_provider import (
    EncryptionTransformation,
)
from tfstate_git.server.adapters.downloaders.age import AgeDownloader
from tfstate_git.server.transformation_providers.transformation_protocol import TransformationProtocol
from tfstate_git.utils.dependency_downloader import DependencyDownloader
from tfstate_git.utils.dependency_manager import DependenciesManager

config = Settings()  # type: ignore

config_file_location = Path.cwd() / "examples" / "tfformer.yaml"
if config_file_location.exists():
    content = config_file_location.read_bytes()
    obj = yaml.safe_load(content)
    file_config = ConfigFile.model_validate(obj)

state = {}


async def initialize_manager() -> DependenciesManager:
    manager = DependenciesManager(
        dependencies=[
            DependencyDownloader(
                names=["age", "age-keygen"],
                version="1.2.0",
                downloader=AgeDownloader(),
            ),
        ],
        dest_folder=config.state_dir,
    )
    await manager.initialize()
    return manager


def create_storage_provider(storage_config: StorageProviderConfig) -> StorageProviderProtocol:
    match storage_config.type:
        case "local":
            return LocalStorageProvider(storage_config.base_dir)

        case "git":
            return GitStorageProvider(
                repo=storage_config.origin_url,
                ref=storage_config.ref,
            )

        case _:
            raise ValueError(f"Unsupported storage provider type: {storage_config.type}")


def generate_encryption_transformer(transformer_config: EncryptionTransformerConfig, config: ConfigFile) -> EncryptionTransformation:
    match transformer_config.key_type:
        case "age":
            # it's safe to get the key because we are past the validation
            key_storage = config.storage_providers[transformer_config.import_from_storage.provider]
            storage_provider = create_storage_provider(key_storage)
            private_key = storage_provider.get_file(transformer_config.import_from_storage.params.path)
            
            

        case _:
            raise ValueError(f"Unsupported encryption key type: {transformer_config.key_type}")


def generate_transformers(config: ConfigFile) -> list[TransformationProtocol]:
    transformers = []
    for transformer in config.transformers:
        match transformer.type:
            case "encryption":
                transformers.append(generate_encryption_transformer(transformer, config))

            case _:
                raise ValueError(f"Unknown transformer type: {transformer.type}")

    return transformers


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    manager = await initialize_manager()

    git_storage_driver = GitStorageProvider(
        repo=config.repo_root_dir,
        ref="main",
    )

    # storage_driver = LocalStorageProvider("/tmp/some_speed")

    age_controller = AgeController(
        binary_location=manager.require_dependency("age"),
    )

    state["controller"] = TFStateLockController(
        storage_driver=git_storage_driver,
        data_transformers=[
            EncryptionTransformation(
                encryption_provider=age_controller,
            ),
        ],
        # terraform config
        state_file=config.state_file,
    )
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
        lock_id: Annotated[
            str, Query(..., alias="ID", description="ID of the state to update")
        ],
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
    uvicorn.run(app, port=port)


if __name__ == "__main__":
    start_server(port=8600)
