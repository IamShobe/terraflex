from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query, Body, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from tfstate_git.server.config import Settings
from tfstate_git.server.repository import GitStateLockRepository, LockingError
from tfstate_git.utils.sops_installer import bootstrap


config = Settings()

state = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    sops_path = await bootstrap(
        config.state_dir,
    )
    state["controller"] = GitStateLockRepository(
        repo=config.repo_root_dir,
        ref="main",
        state_file=config.state_file,
        sops_binary_path=sops_path,
    )
    yield


def get_controller() -> GitStateLockRepository:
    return state["controller"]


ControllerDependency = Annotated[GitStateLockRepository, Depends(get_controller)]


app = FastAPI(lifespan=lifespan)


@app.exception_handler(LockingError)
async def validation_exception_handler(request: Request, exc: LockingError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=jsonable_encoder({"detail": str(exc), "ID": exc.lock_id}),
    )


class LockBody(BaseModel):
    ID: str
    Operation: str
    Who: str
    Version: str
    Created: str


LOCK_STATUS: LockBody | None = None


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
    return controller.lock(body.ID, body)


@app.delete("/lock")
def unlock_state(controller: ControllerDependency):
    return controller.unlock()


def start_server(port: int):
    uvicorn.run(app, port)


if __name__ == "__main__":
    start_server(port=8600)
