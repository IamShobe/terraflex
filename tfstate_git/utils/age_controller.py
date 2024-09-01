from pathlib import Path
from tfstate_git.utils.binary_controller import BinaryController


class AgeKeygenController(BinaryController):
    async def generate_key(self, key_location: Path):
        await self._execute_command(["-o", str(key_location)])

    async def get_public_key(self, key_location: Path):
        with open(key_location, "rb") as f:
            key = f.read()

        return (await self._execute_command(["-y"], input=key)).strip()
