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

    repo_root_dir: pathlib.Path

    state_file: pathlib.Path = pathlib.Path("terraform.tfstate")
