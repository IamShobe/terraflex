import asyncio
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field
import typer
import yaml

from tfstate_git.server.app import initialize_manager, start_server
from tfstate_git.utils.age_controller import AgeKeygenController
from tfstate_git.server.app import config

TFSTATE_REGEX = r"\.tfstate$"

app = typer.Typer()


class CreationRule(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")

    path_regex: Optional[str] = None
    age: Optional[str] = None


class SopsConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")

    creation_rules: list[CreationRule] = Field(default_factory=list)


def create_default_sops_config(age_public_key: str) -> SopsConfig:
    return SopsConfig(
        creation_rules=[CreationRule(path_regex=TFSTATE_REGEX, age=age_public_key)]
    )


def get_existing_age_key(sops_file: Path) -> Optional[str]:
    if sops_file.exists():
        with sops_file.open() as f:
            raw_content = yaml.safe_load(f)

        content = SopsConfig.model_validate(raw_content)
        for rule in content.creation_rules:
            if rule.path_regex is not None and rule.path_regex == TFSTATE_REGEX:
                return rule.age

    return None


def upsert_age_key(age_public_key: str, sops_file: Path):
    if sops_file.exists():
        with sops_file.open() as f:
            raw_content = yaml.safe_load(f)

        content = SopsConfig.model_validate(raw_content)
        for rule in content.creation_rules:
            if rule.path_regex is not None and rule.path_regex == TFSTATE_REGEX:
                rule.age = age_public_key
                break
        else:
            content.creation_rules.append(
                CreationRule(path_regex=TFSTATE_REGEX, age=age_public_key)
            )

    else:
        content = create_default_sops_config(age_public_key)

    sops_file.parent.mkdir(parents=True, exist_ok=True)
    with sops_file.open("w") as f:
        yaml.safe_dump(content.model_dump(), f)


async def use_existing_private_key(
    sops_file: Path,
    age_controller: AgeKeygenController,
    private_key_location: Path,
    force: bool,
) -> Optional[str]:
    public_key = await age_controller.get_public_key(private_key_location)
    existing_public_key = get_existing_age_key(sops_file)
    if existing_public_key is None:  # if no existing key, just add it
        upsert_age_key(public_key, sops_file)
        return None

    if public_key == existing_public_key:
        return public_key  # nothing to do..

    if not force:
        raise typer.Abort(
            f"age key already exists with public key: {existing_public_key}. Use -f to force replacement."
        )

    print("Replacing existing age public key...")
    upsert_age_key(public_key, sops_file)
    return None


async def _init(force: bool):
    manager = await initialize_manager()
    if manager.get_dependency_location("age-keygen") is None:
        raise typer.Abort("age-keygen not found. Please install it first.")

    age_controller = AgeKeygenController(
        binary_location=manager.get_dependency_location("age-keygen"),
        cwd=Path.cwd(),
    )

    sops_file = config.sops_config_path

    private_key_location = config.age_key_path
    if not private_key_location.exists():
        print(
            "Generating new age key... for state encryption at ", private_key_location
        )
        # create the key
        private_key_location.parent.mkdir(parents=True, exist_ok=True)
        await age_controller.generate_key(private_key_location)

    return await use_existing_private_key(
        sops_file, age_controller, private_key_location, force
    )


R = TypeVar("R")


@contextmanager
def capture_aborts():
    try:
        yield
    except typer.Abort as e:
        print("Error:", e)
        raise


@app.command()
def init(
    force: Annotated[
        bool, typer.Option("-f", help="force replacement on existing key")
    ] = False,
):
    with capture_aborts():
        asyncio.run(_init(force))


@app.command()
def export(
    output: Annotated[Path, typer.Argument(..., help="Output file for the key")],
):
    with capture_aborts():
        if not config.age_key_path.exists():
            raise typer.Abort("age key not found. Please initialize it first.")

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(config.age_key_path.read_bytes())


@app.command(name="import")
def import_key(
    file_path: Annotated[Path, typer.Argument(..., help="Input file for the key")],
    force: Annotated[
        bool, typer.Option("-f", help="force replacement on existing key")
    ] = False,
):
    with capture_aborts():
        if not file_path.exists():
            raise typer.Abort("Input file not found")

        config.age_key_path.parent.mkdir(parents=True, exist_ok=True)
        config.age_key_path.write_bytes(file_path.read_bytes())

        asyncio.run(_init(force))


@app.command()
def start(
    port: Annotated[int, typer.Option(help="Port to run the server on")] = 8600,
):
    start_server(port)


def main():
    app()
