import pathlib
from typing import Mapping

from tfstate_git.utils.binary_controller import BinaryController


class Sops(BinaryController):
    def __init__(
        self,
        binary_location: pathlib.Path,
        cwd: pathlib.Path,
        env: Mapping[str, str] = None,
        config: pathlib.Path = None,
    ):
        super().__init__(binary_location, cwd, env)
        self.config = config

    def _get_common_args(self, filename: str):
        args = []
        if self.config is not None:
            args.extend(["--config", str(self.config)])
        
        args.extend([
            "--filename-override",
            filename,
            "--input-type",
            "binary",
            "--output-type",
            "binary",
        ])

        return args

    async def encrypt(self, filename: str, content: str):
        return await self._execute_command(
            [
                *self._get_common_args(filename),
                "--encrypt",
                "/dev/stdin",
            ],
            input=content.encode(),
        )

    async def decrypt(self, filename: str, content: str):
        return await self._execute_command(
            [
                *self._get_common_args(filename),
                "--decrypt",
                "/dev/stdin",
            ],
            input=content.encode(),
        )
