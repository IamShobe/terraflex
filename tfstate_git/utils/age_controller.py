from pathlib import Path
from tfstate_git.utils.binary_controller import BinaryController


class AgeController(BinaryController):
    async def encrypt(self, filename: str, content: str):
        return await self._execute_command(
            [
                *self._get_common_args(filename),
                "--encrypt",
                "/dev/stdin",
            ],
            stdin=content.encode(),
        )

    async def decrypt(self, filename: str, content: str):
        return await self._execute_command(
            [
                *self._get_common_args(filename),
                "--decrypt",
                "/dev/stdin",
            ],
            stdin=content.encode(),
        )


class AgeKeygenController(BinaryController):
    async def generate_key(self, key_location: Path):
        await self._execute_command(["-o", str(key_location)])

    async def get_public_key(self, key_location: Path):
        with open(key_location, "rb") as f:
            key = f.read()

        return (await self._execute_command(["-y"], stdin=key)).strip()
