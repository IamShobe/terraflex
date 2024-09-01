import asyncio
import os
from pathlib import Path
from typing import Annotated, Optional
from pydantic import BaseModel, Field
import typer
import yaml

from tfstate_git.server.app import initialize_manager, start_server
from tfstate_git.utils.age_controller import AgeKeygenController
from tfstate_git.server.app import config

TFSTATE_REGEX = r"\.tfstate$"

app = typer.Typer()


class CreationRule(BaseModel):
    model_config = {
        "from_attributes": True,
        "extra": "allow",
    }

    path_regex: Optional[str] = None
    age: Optional[str] = None


class SopsConfig(BaseModel):
    model_config = {
        "from_attributes": True,
        "extra": "allow",
    }

    creation_rules: list[CreationRule] = Field(default_factory=list)


def create_default_sops_config(age_public_key: str) -> SopsConfig:
    return SopsConfig(
        creation_rules=[CreationRule(path_regex=TFSTATE_REGEX, age=age_public_key)]
    )


def get_existing_age_key(sops_file: str) -> Optional[str]:
    if sops_file.exists():
        with open(sops_file) as f:
            raw_content = yaml.safe_load(f)

        content = SopsConfig.model_validate(raw_content)
        for rule in content.creation_rules:
            if rule.path_regex is not None and rule.path_regex == TFSTATE_REGEX:
                return rule.age

    return None


def upsert_age_key(age_public_key: str, sops_file: str):
    if sops_file.exists():
        with open(sops_file) as f:
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
    with open(sops_file, "w") as f:
        yaml.safe_dump(content.model_dump(), f)


async def use_existing_private_key(
    sops_file: Path, age_controller: AgeKeygenController, private_key_location: Path, force: bool
) -> Optional[str]:
    public_key = await age_controller.get_public_key(private_key_location)
    existing_public_key = get_existing_age_key(sops_file)
    if existing_public_key is None:  # if no existing key, just add it
        upsert_age_key(public_key, sops_file)
        return

    if public_key == existing_public_key:
        return public_key  # nothing to do..

    if not force:
        raise typer.Abort(
            f"age key already exists with public key: {existing_public_key}. Use -f to force replacement."
        )

    print("Replacing existing age public key...")
    upsert_age_key(public_key, sops_file)
    return


async def _init(force: bool):
    manager = await initialize_manager()
    if manager.get_dependency_location("age-keygen") is None:
        raise typer.Abort("age-keygen not found. Please install it first.")

    age_controller = AgeKeygenController(
        binary_location=manager.get_dependency_location("age-keygen"),
        cwd=Path.cwd(),
    )

    sops_file = config.repo_root_dir / config.metadata_dir / "sops.yaml" 

    private_key_location = config.age_key_path
    if not private_key_location.exists():
        print(
            "Generating new age key... for state encryption at ", private_key_location
        )
        # create the key
        private_key_location.parent.mkdir(parents=True, exist_ok=True)
        await age_controller.generate_key(private_key_location)

    return await use_existing_private_key(sops_file, age_controller, private_key_location, force)


@app.command()
def init(
    force: Annotated[
        bool, typer.Option("-f", help="force replacement on existing key")
    ] = False,
):
    try:
        asyncio.run(_init(force))
    
    except typer.Abort as e:
        print("Error:", e)
        raise


@app.command()
def start(
    port: Annotated[int, typer.Option(help="Port to run the server on")] = 8600,
):
    start_server(port)


def main():
    app()
