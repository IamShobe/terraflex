import pathlib
from enum import StrEnum
from typing import (
    Annotated,
    Any,
    Literal,
    Optional,
    Self,
    Type,
    Union,
    get_args,
)

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import (
    BaseSettings,
)
import xdg_base_dirs

PACKAGE_NAME = "tfstate-git"


class StorageProviderType(StrEnum):
    LOCAL = "local"
    GIT = "git"


class GitStorageProviderConfig(BaseModel):
    type: Literal[StorageProviderType.GIT]
    origin_url: str
    clone_dir: pathlib.Path = Field(default=pathlib.Path.cwd())


class LocalStorageProviderConfig(BaseModel):
    type: Literal[StorageProviderType.LOCAL]
    base_dir: pathlib.Path = Field(default=pathlib.Path.cwd())


class LocalStorageProviderUsageParams(BaseModel):
    path: str


class StorageProviderUsageConfig(BaseModel):
    storage_provider: str
    storage_params: Optional[Any]


class EncryptionTransformerConfig(BaseModel):
    type: Literal["encryption"]
    key_type: Literal["age"]  # add more key types here as union
    import_from: StorageProviderUsageConfig


StorageProviderConfig = Annotated[
    Union[LocalStorageProviderConfig, GitStorageProviderConfig],
    Field(discriminator="type"),
]

TransformerConfig = Annotated[
    EncryptionTransformerConfig,  # add more transformer types here as union
    Field(discriminator="type"),
]


class StateManagerConfig(BaseModel):
    storage_provider: str
    state_file: str


STORAGE_PROVIDER_TYPE_TO_PARAMS: dict[
    StorageProviderType, Optional[Type[BaseModel]]
] = {
    StorageProviderType.LOCAL: LocalStorageProviderUsageParams,
    StorageProviderType.GIT: None,
}


# TODO: move this to a test...
annotated_types = get_args(StorageProviderConfig)
union_types = get_args(annotated_types[0])  # first element is the Union type

registered_config_types = [c.__annotations__["type"] for c in union_types]

# assert all storage providers have a corresponding class in STORAGE_PROVIDER_TYPE_TO_PARAMS
assert all(
    config_type in STORAGE_PROVIDER_TYPE_TO_PARAMS
    for config_type in registered_config_types
)


class ConfigFile(BaseModel):
    version: str
    storage_providers: dict[str, StorageProviderConfig]
    transformers: list[TransformerConfig]
    state_manager: StateManagerConfig

    @model_validator(mode="after")
    def check_transformers_configs(self) -> Self:
        for transformer in self.transformers:
            if transformer.type == "encryption":
                if (
                    transformer.import_from.storage_provider
                    not in self.storage_providers
                ):
                    raise ValueError(
                        f"Storage provider '{transformer.import_from.storage_provider}' not declared in storage_providers"
                    )

                storage_provider_type = self.storage_providers[
                    transformer.import_from.storage_provider
                ].type
                if storage_provider_type not in STORAGE_PROVIDER_TYPE_TO_PARAMS:
                    raise ValueError(
                        f"Storage provider '{transformer.import_from.storage_provider}' does not support encryption"
                    )

                storage_class = STORAGE_PROVIDER_TYPE_TO_PARAMS[storage_provider_type]
                if storage_class is not None:
                    if transformer.import_from.storage_params is None:
                        raise ValueError(
                            f"Storage provider '{transformer.import_from.storage_provider}' requires storage_params"
                        )

                    local_params = storage_class.model_validate(
                        transformer.import_from.storage_params
                    )
                    transformer.import_from.storage_params = local_params

        return self


class Settings(BaseSettings):
    state_dir: Annotated[
        pathlib.Path,
        Field(
            default=xdg_base_dirs.xdg_data_home() / PACKAGE_NAME,
        ),
    ]

    repo_root_dir: Annotated[
        pathlib.Path,
        Field(
            default=pathlib.Path.cwd(),
        ),
    ]

    metadata_dir: Annotated[pathlib.Path, Field(default=pathlib.Path(".tfstate_git"))]

    age_key_path: Annotated[
        pathlib.Path,
        Field(
            default=xdg_base_dirs.xdg_config_home() / PACKAGE_NAME / "age_key.txt",
        ),
    ]

    state_file: pathlib.Path = pathlib.Path("terraform2.tfstate")

    @property
    def sops_config_path(self) -> pathlib.Path:
        return self.metadata_dir / "sops.yaml"


# if __name__ == "__main__":
#     config = Settings()
#     print("key")
