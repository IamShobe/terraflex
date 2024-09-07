import abc


class TransformationProvider(abc.ABC):
    @abc.abstractmethod
    async def on_file_save(self, filename: str, content: str) -> str: ...

    @abc.abstractmethod
    async def on_file_read(self, filename: str, content: str) -> str: ...


if __name__ == "__main__":
    print("hey")
