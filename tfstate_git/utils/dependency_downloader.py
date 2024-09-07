import pathlib
from typing import Collection

from tfstate_git.utils.downloaders.base import DependencyDownloader


class DependenciesManager:
    def __init__(
        self,
        dependencies: Collection[DependencyDownloader],
        *,
        dest_folder: pathlib.Path,
    ) -> None:
        self.dependencies = dependencies
        self.dest_folder = dest_folder

        self._resolved_dependencies: dict[str, pathlib.Path] = {}
        self._is_initialized = False

    async def initialize(self) -> None:
        for downloader in self.dependencies:
            results = await downloader.ensure_installed(self.dest_folder)

            for name, location in results.items():
                self._resolved_dependencies[name] = location

        self._is_initialized = True

    def get_dependency_location(self, name: str) -> pathlib.Path:
        if not self._is_initialized:
            raise RuntimeError("Dependencies have not been initialized")

        if name not in self._resolved_dependencies:
            raise ValueError(f"Dependency {name} has not been resolved")

        return self._resolved_dependencies[name]
