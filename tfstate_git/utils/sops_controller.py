import asyncio
import pathlib


class Sops:
    def __init__(self, binary_location: pathlib.Path, cwd: pathlib.Path):
        self.binary_location = binary_location
        self.cwd = cwd

    async def _execute_command(self, args, input=None):
        proc = await asyncio.create_subprocess_exec(
            self.binary_location,
            *args,
            cwd=self.cwd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate(input)
        if proc.returncode != 0:
            raise Exception(f"Failed to execute sops: {stderr.decode()}")

        return stdout.decode()

    async def encrypt(self, content: str):
        return await self._execute_command(["encrypt", "/dev/stdin"], input=content.encode())

    async def decrypt(self, content: str):
        return await self._execute_command(["decrypt", "/dev/stdin"], input=content.encode())
