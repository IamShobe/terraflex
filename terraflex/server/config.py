import pathlib
from typing import (
    Annotated,
    Optional,
    TypeAlias,
)
from packaging.version import Version

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import (
    BaseSettings,
)
import xdg_base_dirs

PACKAGE_NAME = "terraflex"

CONFIG_VERSION = "2"


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


class StackConfig(BaseModel):
    state_storage: StorageProviderUsageConfig
    transformers: list[str]


class ConfigFile(BaseModel):
    version: str = CONFIG_VERSION
    storage_providers: dict[str, StorageProviderConfig]
    transformers: dict[str, TransformerConfig]
    stacks: dict[str, StackConfig]

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        current_version = Version(value)
        config_version = Version(CONFIG_VERSION)
        if current_version < config_version:
            raise ValueError(
                f"Unsupported version ({current_version} < {config_version}) - please upgrade the config file"
            )

        if current_version > config_version:
            raise ValueError(
                f"Unsupported version ({current_version} > {config_version}) - please check if there is a newer version of {PACKAGE_NAME}"
            )

        return value


class Settings(BaseSettings):
    state_dir: Annotated[
        pathlib.Path,
        Field(
            default=xdg_base_dirs.xdg_data_home() / PACKAGE_NAME,
        ),
    ]
