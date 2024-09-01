from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query, Body, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import uvicorn

from tfstate_git.server.config import Settings
from tfstate_git.server.base_state_lock_provider import LockBody
from tfstate_git.server.encrypted_storage_state_lock_provider import (
    EncryptedStateLockProvider,
    EncryptionConfig,
    LockingError,
)
from tfstate_git.server.storage_providers.git_storage_provider import GitStorageProvider
from tfstate_git.server.storage_providers.local_storage_provider import LocalStorageProvider
from tfstate_git.utils.dependency_downloader import DependenciesManager
from tfstate_git.utils.downloaders.age import AgeDownloader
from tfstate_git.utils.downloaders.base import DependencyDownloader
from tfstate_git.utils.downloaders.sops import SopsDownloader


config = Settings()

state = {}


async def initialize_manager():
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
async def lifespan(_: FastAPI):
    manager = await initialize_manager()

    storage_driver = GitStorageProvider(
        repo=config.repo_root_dir,
        ref="main",
    )

    # storage_driver = LocalStorageProvider("/tmp/some_speed")

    state["controller"] = EncryptedStateLockProvider(
        manager=manager,
        storage_driver=storage_driver,
        encryption_config=EncryptionConfig(
            sops_config_path=config.sops_config_path,
            key_path=config.age_key_path,
        ),
        # terraform config
        state_file=config.state_file,
    )
    yield


def get_controller() -> EncryptedStateLockProvider:
    return state["controller"]


ControllerDependency = Annotated[EncryptedStateLockProvider, Depends(get_controller)]


app = FastAPI(lifespan=lifespan)


@app.exception_handler(LockingError)
async def validation_exception_handler(request: Request, exc: LockingError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=jsonable_encoder({"detail": str(exc), "ID": exc.lock_id}),
    )


@app.get("/state")
async def get_state(controller: ControllerDependency):
    # read the state file
    state = await controller.get()
    if state is None:
        raise HTTPException(status_code=404, detail="State not found")

    return state


@app.post("/state")
async def update_state(
    ID: Annotated[str, Query(..., description="ID of the state to update")],
    state: Annotated[dict, Body(..., description="New state")],
    controller: ControllerDependency,
):
    return await controller.put(ID, state)


@app.delete("/state")
async def delete_state(controller: ControllerDependency):
    return await controller.delete()


@app.put("/lock")
def lock_state(body: LockBody, controller: ControllerDependency):
    return controller.lock(body)


@app.delete("/lock")
def unlock_state(controller: ControllerDependency):
    return controller.unlock()


def start_server(port: int):
    uvicorn.run(app, port=port)


if __name__ == "__main__":
    start_server(port=8600)
