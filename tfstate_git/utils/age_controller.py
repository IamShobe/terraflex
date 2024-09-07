from pathlib import Path
from tfstate_git.utils.binary_controller import BinaryController

ENCODING = "utf-8"


# TODO: WIP
class AgeController(BinaryController):
    pass
    # async def encrypt(self, filename: str, content: str) -> str:
    #     return await self._execute_command(
    #         [
    #             *self._get_common_args(filename),
    #             "--encrypt",
    #             "/dev/stdin",
    #         ],
    #         stdin=content.encode(ENCODING),
    #     )

    # async def decrypt(self, filename: str, content: str) -> str:
    #     return await self._execute_command(
    #         [
    #             *self._get_common_args(filename),
    #             "--decrypt",
    #             "/dev/stdin",
    #         ],
    #         stdin=content.encode(ENCODING),
    #     )


class AgeKeygenController(BinaryController):
    async def generate_key(self, key_location: Path) -> None:
        await self._execute_command(["-o", str(key_location)])

    async def get_public_key(self, key_location: Path) -> str:
        with open(key_location, "rb") as f:
            key = f.read()

        return (await self._execute_command(["-y"], stdin=key)).strip()
