import pathlib
import platform
import tarfile
import tempfile

import httpx

from tfstate_git.utils.downloaders.base import mv_executable_to_dest

AGE_URL_DOWNLOAD = "https://dl.filippo.io/age/v{version}?for={platform}"


class AgeDownloader:
    async def __call__(
        self, version: str, expected_paths: dict[str, pathlib.Path]
    ) -> dict[str, pathlib.Path]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                AGE_URL_DOWNLOAD.format(
                    version=version,
                    platform=f"{platform.system().lower()}/{platform.machine().lower()}",
                ),
                follow_redirects=True,
            )

        if response.status_code != 200:
            raise Exception(
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
                raise Exception("Expected age to be in the expected paths")

            mv_executable_to_dest(age_bin, expected_paths["age"])

            age_keygen = pathlib.Path(tmp_dir) / "age" / "age-keygen"
            if "age-keygen" not in expected_paths:
                raise Exception("Expected age-keygen to be in the expected paths")

            mv_executable_to_dest(age_keygen, expected_paths["age-keygen"])