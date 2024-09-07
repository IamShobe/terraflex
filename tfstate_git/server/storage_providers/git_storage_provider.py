from contextlib import suppress
import pathlib
import subprocess

from tfstate_git.server.base_state_lock_provider import LockBody
from tfstate_git.server.tf_state_lock_controller import (
    assume_lock_conflict_on_error,
)
from tfstate_git.server.storage_providers.base_storage_provider import StorageProvider


class GitStorageProvider(StorageProvider):
    """This follows the steps described in the suggestion here:
    https://github.com/plumber-cd/terraform-backend-git
    """

    def __init__(self, repo: pathlib.Path, ref: str = "main") -> None:
        self.repo = repo
        self.ref = ref

    def _git(self, command: str, *args: str) -> str:
        proc = subprocess.run(
            ["git", command, *args],
            cwd=self.repo,
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

    def get_file(self, file_name: str) -> str | None:
        self._cleanup_workspace()
        # pull latest changes
        self._git("pull", "origin", self.ref)

        # read state
        state_file = self.repo / file_name
        try:
            return state_file.read_text()

        except FileNotFoundError:
            return None

    def put_file(self, file_name: str, data: str) -> None:
        self._cleanup_workspace()
        # pull latest changes
        self._git("pull", "origin", self.ref)

        # save state
        state_file = self.repo / file_name
        state_file.write_text(data)

        self._git("add", str(state_file))
        self._git("commit", "-m", f"Update state - {file_name}")
        self._git("push", "origin", self.ref)

    def delete_file(self, file_name: str) -> None:
        self._cleanup_workspace()
        # pull latest changes
        self._git("pull", "origin", self.ref)

        # delete state
        state_file = self.repo / file_name
        state_file.unlink()

        self._git("add", str(state_file))
        self._git("commit", "-m", f"Delete state - {file_name}")
        self._git("push", "origin", self.ref)

    def read_lock(self, file_name: str) -> bytes | None:
        self._cleanup_workspace()
        # delete lock branch if it exists
        with suppress(Exception):
            self._git("branch", "-D", f"locks/{file_name}")
        # pull latest changes
        self._git("fetch", "origin", "refs/heads/locks/*:refs/remotes/origin/locks/*")

        try:
            self._git("checkout", f"locks/{file_name}")

        except RuntimeError:
            return None

        # read lock data
        lock_file = self.repo / "locks" / f"{file_name}.lock"
        return lock_file.read_bytes()

    def acquire_lock(self, file_name: str, data: LockBody) -> None:
        self._cleanup_workspace()
        # delete lock branch if it exists
        with suppress(Exception):
            self._git("branch", "-D", f"locks/{file_name}")
        # pull latest changes
        self._git("pull", "origin", self.ref)

        # create a new locking branch
        self._git("checkout", "-b", f"locks/{file_name}")

        # make sure lock folder exists
        locks_dir = self.repo / "locks"
        locks_dir.mkdir(exist_ok=True)
        # write lock file
        lock_file = locks_dir / f"{file_name}.lock"
        lock_file.write_bytes(data.model_dump_json().encode())

        self._git("add", str(lock_file))
        self._git("commit", "-m", f"Locking state - id {data.ID}")
        with assume_lock_conflict_on_error(lock_id=data.ID):
            self._git("push", "origin", f"locks/{file_name}")

    def release_lock(self, file_name: str) -> None:
        self._git("push", "origin", "--delete", f"locks/{file_name}")
