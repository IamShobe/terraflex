from pathlib import Path
import tempfile

from terraflex.utils.binary_controller import BinaryController


class AgeController(BinaryController):
    def __init__(
        self,
        binary_location: Path,
        private_key: bytes,
        public_key: bytes,
    ):
        super().__init__(binary_location)
        self.private_key = private_key
        self.public_key = public_key

    async def encrypt(self, _: str, content: bytes) -> bytes:
        return await self._execute_command(
            [
                "--encrypt",
                "-r",
                self.public_key,
            ],
            stdin=content,
        )

    async def decrypt(self, _: str, content: bytes) -> bytes:
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(self.private_key)
            temp.flush()

            return await self._execute_command(
                [
                    "--decrypt",
                    "-i",
                    temp.name,
                ],
                stdin=content,
            )


class AgeKeygenController(BinaryController):
    async def generate_key_bytes(self) -> bytes:
        return (await self._execute_command([])).strip()

    async def generate_key(self, key_location: Path) -> None:
        key_bytes = await self.generate_key_bytes()
        key_location.write_bytes(key_bytes)

    async def get_public_key(self, key_location: Path) -> bytes:
        key = key_location.read_bytes()
        return await self.get_public_key_from_bytes(key)

    async def get_public_key_from_bytes(self, content: bytes) -> bytes:
        return (await self._execute_command(["-y"], stdin=content)).strip()
