from contextlib import suppress
import pathlib
import subprocess
from typing import Any, Optional, Self, override

from pydantic import BaseModel

from tfstate_git.server.base_state_lock_provider import LockBody

from tfstate_git.server.storage_provider_base import (
    ItemKey,
    AbstractStorageProvider,
    assume_lock_conflict_on_error,
)
from tfstate_git.utils.dependency_manager import DependenciesManager


class GitStorageProviderItemIdentifier(ItemKey):
    path: str

    def as_string(self) -> str:
        return self.path


class GitStorageProviderInitConfig(BaseModel):
    origin_url: str
    ref: Optional[str] = "main"
    clone_path: Optional[pathlib.Path] = None


def directory_is_empty(directory: pathlib.Path) -> bool:
    return not any(directory.iterdir())


class GitStorageProvider(AbstractStorageProvider):
    """This follows the steps described in the suggestion here:
    https://github.com/plumber-cd/terraform-backend-git
    """

    def __init__(
        self,
        origin_url: str,
        clone_path: pathlib.Path,
        ref: str = "main",
    ) -> None:
        self.clone_path = clone_path.expanduser()
        self.origin_url = origin_url
        self.ref = ref

        self._initialize()

    def _initialize(self) -> None:
        # create parent directories
        self.clone_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.clone_path.exists():
            # clone the repository
            self._git("clone", self.origin_url, str(self.clone_path), cwd=self.clone_path.parent)

        self.validate()

    # TODO: Add invoking for this method...
    def validate(self) -> None:
        # check that the path isn't dirty
        if not self.clone_path.exists():
            raise FileNotFoundError(f"Path {self.clone_path} does not exist")

        if not self.clone_path.is_dir():
            raise NotADirectoryError(f"Path {self.clone_path} is not a directory")

        if not (self.clone_path / ".git").exists():
            raise FileNotFoundError(f"Path {self.clone_path} is not a git repository")

        if self._is_dirty():
            raise RuntimeError(
                f"Path {self.clone_path} is dirty - please commit or stash changes before using this provider"
            )

    @override
    @classmethod
    async def from_config(
        cls,
        raw_config: Any,
        *,
        manager: DependenciesManager,
        workdir: pathlib.Path,
    ) -> Self:
        result = GitStorageProviderInitConfig.model_validate(raw_config)

        repo_name = result.origin_url.split("/")[-1].replace(".git", "")
        result.clone_path = result.clone_path or (workdir / "git_storage" / repo_name)

        return cls(
            **result.model_dump(),
        )

    def _git(self, command: str, *args: str, cwd=None) -> str:
        proc = subprocess.run(
            ["git", command, *args],
            cwd=cwd or self.clone_path,
            capture_output=True,
            text=True,
            check=False,
        )

        if proc.returncode != 0:
            raise RuntimeError(f"Error running git command: {proc.stderr}")

        return proc.stdout

    def _cleanup_workspace(self) -> None:
        self._git("reset", "--hard")
        self._git("checkout", self.ref)

    def _is_dirty(self) -> bool:
        return bool(self._git("status", "--porcelain"))

    @override
    @classmethod
    def validate_key(cls, key: dict) -> GitStorageProviderItemIdentifier:
        return GitStorageProviderItemIdentifier.model_validate(key)

    @override
    def get_file(self, item_identifier: GitStorageProviderItemIdentifier) -> bytes:
        file_name = item_identifier.path
        self._cleanup_workspace()
        # pull latest changes
        self._git("pull", "origin", self.ref)

        # read state
        state_file = self.clone_path / file_name
        try:
            return state_file.read_bytes()

        except FileNotFoundError as exc:
            raise FileNotFoundError(f"File {file_name} not found in the repository") from exc

    def commit_and_push_changes(self, message: str, ref=None) -> None:
        self._git("add", ".")
        self._git("commit", "-m", message)
        self._git("push", "origin", ref or self.ref)

    @override
    def put_file(self, item_identifier: GitStorageProviderItemIdentifier, data: bytes) -> None:
        file_name = item_identifier.path
        self._cleanup_workspace()
        # pull latest changes
        self._git("pull", "origin", self.ref)

        # save state
        state_file = self.clone_path / file_name
        state_file.write_bytes(data)

        self.commit_and_push_changes(f"Update state - {file_name}")

    @override
    def delete_file(self, item_identifier: GitStorageProviderItemIdentifier) -> None:
        file_name = item_identifier.path
        self._cleanup_workspace()
        # pull latest changes
        self._git("pull", "origin", self.ref)

        # delete state
        state_file = self.clone_path / file_name
        state_file.unlink()

        self.commit_and_push_changes(f"Delete state - {file_name}")

    @override
    def read_lock(self, item_identifier: GitStorageProviderItemIdentifier) -> bytes:
        file_name = item_identifier.path
        self._cleanup_workspace()
        # delete lock branch if it exists
        with suppress(Exception):
            self._git("branch", "-D", f"locks/{file_name}")
        # pull latest changes
        self._git("fetch", "origin", "refs/heads/locks/*:refs/remotes/origin/locks/*")

        try:
            self._git("checkout", f"locks/{file_name}")

        except RuntimeError as exc:
            raise FileNotFoundError(f"Lock file {file_name} not found in the repository") from exc

        # read lock data
        lock_file = self.clone_path / "locks" / f"{file_name}.lock"
        return lock_file.read_bytes()

    @override
    def acquire_lock(self, item_identifier: GitStorageProviderItemIdentifier, data: LockBody) -> None:
        file_name = item_identifier.path
        self._cleanup_workspace()
        # delete lock branch if it exists
        with suppress(Exception):
            self._git("branch", "-D", f"locks/{file_name}")
        # pull latest changes
        self._git("pull", "origin", self.ref)

        # create a new locking branch
        self._git("checkout", "-b", f"locks/{file_name}")

        # make sure lock folder exists
        locks_dir = self.clone_path / "locks"
        locks_dir.mkdir(exist_ok=True)
        # write lock file
        lock_file = locks_dir / f"{file_name}.lock"
        lock_file.write_bytes(data.model_dump_json().encode())

        self._git("add", str(lock_file))
        self._git("commit", "-m", f"Locking state - id {data.ID}")
        with assume_lock_conflict_on_error(lock_id=data.ID):
            self._git("push", "origin", f"locks/{file_name}")

    @override
    def release_lock(self, item_identifier: GitStorageProviderItemIdentifier) -> None:
        file_name = item_identifier.path
        self._git("push", "origin", "--delete", f"locks/{file_name}")
