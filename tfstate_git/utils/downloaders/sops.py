import pathlib
import platform

import httpx

from tfstate_git.utils.downloaders.base import write_executable_to_file


class SopsDownloader:
    async def __call__(
        self, version: str, expected_paths: dict[str, pathlib.Path]
    ) -> dict[str, pathlib.Path]:
        bin_name = (
            f"sops-v{version}.{platform.system().lower()}.{platform.machine().lower()}"
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://github.com/getsops/sops/releases/download/v{version}/{bin_name}",
                follow_redirects=True,
            )

        if response.status_code != 200:
            raise Exception(
                f"Failed to download sops: {response.status_code} - {response.text}"
            )

        if "sops" not in expected_paths:
            raise Exception("Expected sops to be in the expected paths")

        write_executable_to_file(expected_paths["sops"], response.content)
