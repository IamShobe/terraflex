import pathlib

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import xdg_base_dirs

PACKAGE_NAME = "tfstate-git"


class Settings(BaseSettings):
    model_config = SettingsConfigDict()

    state_dir: pathlib.Path = Field(
        default=xdg_base_dirs.xdg_data_home() / PACKAGE_NAME,
    )

    repo_root_dir: pathlib.Path = Field(
        default=pathlib.Path.cwd(),
    )

    metadata_dir: pathlib.Path = Field(default=".tfstate_git")

    age_key_path: pathlib.Path = Field(
        default=xdg_base_dirs.xdg_config_home() / PACKAGE_NAME / "age_key.txt",
    )

    state_file: pathlib.Path = pathlib.Path("terraform2.tfstate")

    @property
    def sops_config_path(self) -> pathlib.Path:
        return self.metadata_dir / "sops.yaml"
