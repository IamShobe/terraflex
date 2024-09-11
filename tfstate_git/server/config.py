import pathlib
from typing import (
    Annotated,
    Optional,
    TypeAlias,
)

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import (
    BaseSettings,
)
import xdg_base_dirs

PACKAGE_NAME = "tfstate-git"


StorageParams: TypeAlias = dict


class StorageProviderUsageConfig(BaseModel):
    provider: str
    params: Optional[StorageParams]


class StorageProviderConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str


class TransformerConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str


class StateManagerConfig(BaseModel):
    storage: StorageProviderUsageConfig


class ConfigFile(BaseModel):
    version: str
    storage_providers: dict[str, StorageProviderConfig]
    transformers: list[TransformerConfig]
    state_manager: StateManagerConfig


class Settings(BaseSettings):
    state_dir: Annotated[
        pathlib.Path,
        Field(
            default=xdg_base_dirs.xdg_data_home() / PACKAGE_NAME,
        ),
    ]

    metadata_dir: Annotated[pathlib.Path, Field(default=pathlib.Path(".tfstate_git"))]
