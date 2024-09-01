import asyncio
import pathlib


class BinaryController:
    def __init__(self, binary_location: pathlib.Path, cwd: pathlib.Path, env=None):
        self.binary_location = binary_location
        self.cwd = cwd
        self.env = env or {}

    async def _execute_command(self, args, input=None):
        proc = await asyncio.create_subprocess_exec(
            self.binary_location,
            *args,
            cwd=self.cwd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self.env,
        )

        stdout, stderr = await proc.communicate(input)
        if proc.returncode != 0:
            raise Exception(f"Failed to execute binary: {stderr.decode()}")

        return stdout.decode()
