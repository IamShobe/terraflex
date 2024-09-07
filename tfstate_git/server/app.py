from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncIterator
from fastapi import Depends, FastAPI, HTTPException, Query, Body, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import uvicorn

from tfstate_git.server.config import Settings
from tfstate_git.server.base_state_lock_provider import (
    BaseStateLockProvider,
    Data,
    LockBody,
    LockingError,
)
from tfstate_git.server.tf_state_lock_controller import (
    TFStateLockController,
)
from tfstate_git.server.storage_providers.git_storage_provider import GitStorageProvider
from tfstate_git.server.transformation_providers.encryption_transformation_provider import (
    EncryptionConfig,
    EncryptionTransformationProvider,
)
from tfstate_git.utils.dependency_downloader import DependenciesManager
from tfstate_git.utils.downloaders.age import AgeDownloader
from tfstate_git.utils.downloaders.base import DependencyDownloader
from tfstate_git.utils.downloaders.sops import SopsDownloader


config = Settings()  # type: ignore

state = {}


async def initialize_manager() -> DependenciesManager:
    manager = DependenciesManager(
        dependencies=[
            DependencyDownloader(
                names=["sops"],
                version="3.9.0",
                download_file_callback=SopsDownloader(),
            ),
            DependencyDownloader(
                names=["age", "age-keygen"],
                version="1.2.0",
                download_file_callback=AgeDownloader(),
            ),
        ],
        dest_folder=config.state_dir,
    )
    await manager.initialize()
    return manager


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    manager = await initialize_manager()

    git_storage_driver = GitStorageProvider(
        repo=config.repo_root_dir,
        ref="main",
    )

    # storage_driver = LocalStorageProvider("/tmp/some_speed")

    state["controller"] = TFStateLockController(
        storage_driver=git_storage_driver,
        data_transformers=[
            EncryptionTransformationProvider(
                storage_driver=git_storage_driver,
                manager=manager,
                encryption_config=EncryptionConfig(
                    sops_config_path=config.sops_config_path,
                    key_path=config.age_key_path,
                ),
            )
        ],
        # terraform config
        state_file=config.state_file,
    )
    yield


def get_controller() -> BaseStateLockProvider:
    return state["controller"]


ControllerDependency = Annotated[BaseStateLockProvider, Depends(get_controller)]


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
