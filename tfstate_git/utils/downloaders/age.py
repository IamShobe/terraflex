import pathlib
import platform
import tarfile
import tempfile
from typing import override

import httpx

from tfstate_git.utils.downloaders.base import BaseDownloader, mv_executable_to_dest

# pylint: disable=line-too-long
AGE_URL_DOWNLOAD = "https://github.com/FiloSottile/age/releases/download/v{version}/age-v{version}-{platform}.tar.gz"


class AgeDownloader(BaseDownloader):
    @override
    async def __call__(self, version: str, expected_paths: dict[str, pathlib.Path]):
        url = AGE_URL_DOWNLOAD.format(
            version=version,
            # TODO: implement better support
            platform=f"{platform.system().lower()}-amd64",
        )
        print("downloading age from", url)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                follow_redirects=True,
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to download age: {response.status_code} - {response.text}"
            )

        with tempfile.TemporaryDirectory() as tmp_dir:
            with tempfile.NamedTemporaryFile() as temp:
                temp.write(response.content)
                temp.flush()

                with tarfile.open(temp.name, "r") as tar:
                    tar.extractall(tmp_dir)

            age_bin = pathlib.Path(tmp_dir) / "age" / "age"
            if "age" not in expected_paths:
                raise ValueError("Expected age to be in the expected paths")

            mv_executable_to_dest(age_bin, expected_paths["age"])

            age_keygen = pathlib.Path(tmp_dir) / "age" / "age-keygen"
            if "age-keygen" not in expected_paths:
                raise ValueError("Expected age-keygen to be in the expected paths")

            mv_executable_to_dest(age_keygen, expected_paths["age-keygen"])
