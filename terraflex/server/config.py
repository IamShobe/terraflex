import pathlib
from typing import (
    Annotated,
    Any,
    Optional,
)

import semver
import xdg_base_dirs
from pydantic_settings import (
    BaseSettings,
)

from pydantic import BaseModel, ConfigDict, Field, field_validator

PACKAGE_NAME = "terraflex"

CONFIG_VERSION = "2"


class StorageProviderUsageConfig(BaseModel):
    """Data struct that contains the parameters that link to a specific file in a given storage provider.

    Each storage provider defines it's own unique usage parameters.

    Please refer to your storage provider usage config for key specification.

    Attributes:
        provider: storage provider name defined in `storage_providers` section of the config file.
        params: storage provider specific usage parameters - each storage provider defines it's own params -
            and this dict will be processed and validated dynamically by each storage provider.

    Example:
        This is an example of a `local` storage provider usage config:
        ```yaml
        provider: local
        params:
            path: ./path/to/item.txt
        ```
    """

    provider: str
    params: Optional[dict[str, Any]] = None


class StorageProviderConfig(BaseModel):
    """Data struct that contains the configuration for a storage provider.

    Each storage provider defines it's own unique configuration parameters -
    and the parameters will be passed through to the storage provider.

    Attributes:
        type: storage provider type as declared in the entrypoint.
        **kwargs: storage provider specific configuration parameters.

    Example:
        In this example, the `local` storage provider has a `folder` parameter that is required.
        The storage provider will get a dict: `{"folder": "/path/to/folder"}` as the configuration.

        ```yaml
        type: local
        folder: /path/to/folder
        ```
    """

    model_config = ConfigDict(extra="allow")
    type: str


class TransformerConfig(BaseModel):
    """Base Transformer configuration.

    Each transformer defines it's own unique configuration parameters -
    and the parameters will be passed through to the transformer.

    Attributes:
        type: The type of the transformer.
        **kwargs: Additional configuration for the transformer.
    """

    model_config = ConfigDict(extra="allow")
    type: str


class StackConfig(BaseModel):
    """Configuration for a terraform stack.

    Attributes:
        state_storage: The storage provider configuration for the state file.
        transformers: The list of transformers to apply to the data.
    """

    state_storage: StorageProviderUsageConfig
    transformers: list[str]


class ConfigFile(BaseModel):
    """The configuration file for terraflex.

    Attributes:
        version: The version of the configuration file.
        storage_providers: The configuration for the storage providers.
        transformers: The configuration for the transformers.
        stacks: The configuration for the stacks.
    """

    version: str = CONFIG_VERSION
    storage_providers: dict[str, StorageProviderConfig]
    transformers: dict[str, TransformerConfig]
    stacks: dict[str, StackConfig]

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        current_version = semver.Version.parse(value, optional_minor_and_patch=True)
        config_version = semver.Version.parse(CONFIG_VERSION, optional_minor_and_patch=True)
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
