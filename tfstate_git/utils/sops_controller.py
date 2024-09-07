import tempfile
import pathlib
from typing import Mapping, Optional

from tfstate_git.utils.binary_controller import BinaryController

ENCODING = "utf-8"


class Sops(BinaryController):
    def __init__(
        self,
        binary_location: pathlib.Path,
        cwd: Optional[pathlib.Path] = None,
        env: Optional[Mapping[str, str]] = None,
        config: Optional[str] = None,
    ):
        super().__init__(binary_location, cwd, env)
        self.config = config

        self._cached_config_file: pathlib.Path | None = None

    @property
    def config_file(self) -> pathlib.Path | None:
        # write the config to a temporary file
        if self.config is None:
            return None

        if self._cached_config_file is not None:
            if self._cached_config_file.exists():
                return self._cached_config_file

        tmp_file = pathlib.Path(tempfile.mktemp(".yaml"))
        tmp_file.write_text(self.config, encoding=ENCODING)

        self._cached_config_file = pathlib.Path(tmp_file)
        return self._cached_config_file

    def _get_common_args(self, filename: str) -> list[str]:
        args = []
        if self.config is not None:
            args.extend(["--config", str(self.config_file)])

        args.extend(
            [
                "--filename-override",
                filename,
                "--input-type",
                "binary",
                "--output-type",
                "binary",
            ]
        )

        return args

    async def encrypt(self, filename: str, content: str) -> str:
        return await self._execute_command(
            [
                *self._get_common_args(filename),
                "--encrypt",
                "/dev/stdin",
            ],
            stdin=content.encode(ENCODING),
        )

    async def decrypt(self, filename: str, content: str) -> str:
        return await self._execute_command(
            [
                *self._get_common_args(filename),
                "--decrypt",
                "/dev/stdin",
            ],
            stdin=content.encode(ENCODING),
        )
