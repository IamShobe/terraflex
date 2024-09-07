import pathlib
import platform
from typing import override

import httpx

from tfstate_git.utils.downloaders.base import BaseDownloader, write_executable_to_file


class SopsDownloader(BaseDownloader):
    @override
    async def __call__(self, version: str, expected_paths: dict[str, pathlib.Path]):
        arch = platform.machine().lower()
        if arch == "x86_64":
            arch = "amd64"

        elif arch == "aarch64":
            arch = "arm64"

        bin_name = f"sops-v{version}.{platform.system().lower()}.{arch}"
        print(bin_name)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://github.com/getsops/sops/releases/download/v{version}/{bin_name}",
                follow_redirects=True,
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to download sops: {response.status_code} - {response.text}"
            )

        if "sops" not in expected_paths:
            raise ValueError("Expected sops to be in the expected paths")

        write_executable_to_file(expected_paths["sops"], response.content)
