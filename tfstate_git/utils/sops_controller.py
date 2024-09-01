import tempfile
import pathlib
from typing import Mapping

from tfstate_git.utils.binary_controller import BinaryController


class Sops(BinaryController):
    def __init__(
        self,
        binary_location: pathlib.Path,
        cwd: pathlib.Path = None,
        env: Mapping[str, str] = None,
        config: str = None,
    ):
        super().__init__(binary_location, cwd, env)
        self.config = config

        self._cached_config_file: pathlib.Path | None = None
    
    @property
    def config_file(self):
        # write the config to a temporary file
        if self.config is None:
            return None
        
        if self._cached_config_file is not None:
            if self._cached_config_file.exists():
                return self._cached_config_file
            
        tmp_file = pathlib.Path(tempfile.mktemp(".yaml"))
        tmp_file.write_text(self.config)

        self._cached_config_file = pathlib.Path(tmp_file)
        return self._cached_config_file
        
    def _get_common_args(self, filename: str):
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
