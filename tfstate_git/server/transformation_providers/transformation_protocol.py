from typing import Protocol


class TransformationProtocol(Protocol):
    async def transform_write_file_content(self, filename: str, content: bytes) -> bytes: ...
    async def transform_read_file_content(self, filename: str, content: bytes) -> bytes: ...


if __name__ == "__main__":
    print("hey")
