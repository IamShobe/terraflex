import abc
import pathlib
from typing import Any, Self

from tfstate_git.server.storage_provider_base import AbstractStorageProvider
from tfstate_git.utils.dependency_manager import DependenciesManager


TRANSFORMERS_ENTRYPOINT = "tfformer.plugins.transformer"


class AbstractTransformation(abc.ABC):
    @classmethod
    @abc.abstractmethod
    async def from_config(
        cls,
        raw_config: Any,
        *,
        storage_providers: dict[str, AbstractStorageProvider],
        manager: DependenciesManager,
        workdir: pathlib.Path,
    ) -> Self: ...

    @abc.abstractmethod
    async def transform_write_file_content(self, file_identifier: str, content: bytes) -> bytes: ...

    @abc.abstractmethod
    async def transform_read_file_content(self, file_identifier: str, content: bytes) -> bytes: ...


if __name__ == "__main__":
    print("hey")
