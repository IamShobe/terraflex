import asyncio
import pathlib
from typing import Mapping, Optional


class BinaryController:
    def __init__(
        self,
        binary_location: pathlib.Path,
        cwd: Optional[pathlib.Path] = None,
        env: Optional[Mapping[str, str]] = None,
    ):
        self.binary_location = binary_location
        self.cwd = cwd
        self.env = env or {}

    async def _execute_command(
        self, args: list[str], stdin: Optional[bytes] = None,
    ) -> str:
        proc = await asyncio.create_subprocess_exec(
            self.binary_location,
            *args,
            cwd=self.cwd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self.env,
        )

        stdout, stderr = await proc.communicate(stdin)
        if proc.returncode != 0:
            raise RuntimeError(f"Failed to execute binary: {stderr.decode()}")

        return stdout.decode()
