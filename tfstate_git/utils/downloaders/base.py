import abc
import pathlib
from typing import Awaitable, Callable


def mv_executable_to_dest(src: pathlib.Path, dest: pathlib.Path) -> None:
    # check if equal to dest
    if src == dest:
        return

    # check if dest exists - remove it
    if dest.exists():
        dest.unlink()

    src.rename(dest)
    dest.chmod(0o755)


def should_download(expected_locations: dict[str, pathlib.Path]) -> bool:
    return not all([location.exists() for location in expected_locations.values()])


def write_executable_to_file(output_bin: pathlib.Path, content: bytes) -> None:
    with open(output_bin, "wb") as f:
        f.write(content)

    output_bin.chmod(0o755)


class BaseDownloader(abc.ABC):
    @abc.abstractmethod
    async def __call__(self, version: str, expected_paths: dict[str, pathlib.Path]) -> None: ...


class DependencyDownloader:
    def __init__(
        self,
        names: list[str],
        version: str,
        download_file_callback: Callable[
            [str, dict[str, pathlib.Path]], Awaitable[None]
        ],
    ):
        self.names = names
        self.version = version
        self.download_file_callback = download_file_callback

    def get_bin_names(self) -> dict[str, str]:
        return {name: f"{name}-v{self.version}" for name in self.names}

    def get_expected_locations(
        self, dest_folder: pathlib.Path
    ) -> dict[str, pathlib.Path]:
        bin_names = self.get_bin_names()
        return {name: (dest_folder / bin_name) for name, bin_name in bin_names.items()}

    async def ensure_installed(self, dest_folder: pathlib.Path) -> dict[str, pathlib.Path]:
        expected_locations = self.get_expected_locations(dest_folder)
        if should_download(expected_locations):
            # create directory if it doesn't exist
            dest_folder.mkdir(parents=True, exist_ok=True)
            return await self._download(expected_locations)

        return expected_locations

    async def _download(self, expected_locations: dict[str, pathlib.Path]) -> dict[str, pathlib.Path]:
        print(f"Downloading {self.names} client...")
        await self.download_file_callback(self.version, expected_locations)
        return expected_locations
