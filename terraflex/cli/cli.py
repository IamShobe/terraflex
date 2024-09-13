import asyncio
from contextlib import contextmanager
import multiprocessing
import subprocess
import pathlib
import time
from typing import Annotated, Iterator
import httpx
import typer
from uvicorn import Config, Server
import yaml
import questionary

from terraflex.cli.builders.wizard import start_configfile_creation_wizard
from terraflex.server.app import (
    CONFIG_FILE_NAME,
    READY_MESSAGE,
    initialize_manager,
    start_server,
    app as server_app,
)


app = typer.Typer(pretty_exceptions_enable=False)


@contextmanager
def capture_aborts() -> Iterator[None]:
    try:
        yield
    except typer.Abort as e:
        print("Error:", e)
        raise


async def _init() -> None:
    manager = await initialize_manager()
    config_file_location = pathlib.Path(CONFIG_FILE_NAME)
    if config_file_location.exists():
        print("Configuration file already exists")
        should_replace = await questionary.confirm(
            "Do you want to replace it?",
            default=False,
        ).ask_async()
        if not should_replace:
            print("Aborting...")
            return

        print("Replacing existing configuration file")

    result_file = await start_configfile_creation_wizard(manager)
    raw_file = yaml.safe_dump(yaml.safe_load(result_file.model_dump_json()))
    config_file_location.write_text(raw_file, encoding="utf-8")

    print("\n\n")
    print("Configuration file created")
    print("You can now start the server with `terraflex start`")
    print("In terraform backend configuration, use the following:\n")
    print(READY_MESSAGE.format(port=8600))


@app.command()
def init() -> None:
    with capture_aborts():
        asyncio.run(_init())


@app.command()
def start(
    port: Annotated[int, typer.Option(help="Port to run the server on")] = 8600,
) -> None:
    start_server(port)


class UvicornServer(multiprocessing.Process):
    def __init__(self, config: Config):
        super().__init__()
        self.server = Server(config=config)
        self.config = config

    def stop(self):
        self.terminate()

    def run(self, *args, **kwargs):
        self.server.run()


def wait_until_ready(port: int):
    client = httpx.Client()
    while True:
        try:
            response = client.get(f"http://localhost:{port}/ready")
            response.raise_for_status()
            break
        except Exception:
            time.sleep(0.2)


@app.command()
def wrap(
    verbose: Annotated[
        bool,
        typer.Option("-v", "--verbose", help="Print more details about the backend"),
    ] = False,
    port: Annotated[int, typer.Option(help="Port to run the server on")] = 8600,
    args: list[str] = typer.Argument(help="Command to run"),
) -> None:
    instance = UvicornServer(
        config=Config(
            app=server_app,
            port=port,
            access_log=verbose,
            log_level="info" if verbose else "warning",
        )
    )
    instance.start()
    wait_until_ready(port)
    # run the command
    subprocess.run(args)
    instance.stop()


def main() -> None:
    app()
