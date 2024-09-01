import abc
from contextlib import suppress
import json
import os
import pathlib
import subprocess
from pydantic import BaseModel

from tfstate_git.utils.sops_controller import Sops


class LockBody(BaseModel):
    model_config = {
        "from_attributes": True,
    }

    ID: str
    Operation: str
    Who: str
    Version: str
    Created: str


class LockingError(Exception):
    def __init__(self, msg: str, lock_id: str) -> None:
        super().__init__(msg)
        self.lock_id = lock_id


class BaseStateLockRepository(abc.ABC):
    @abc.abstractmethod
    async def get(self): ...

    @abc.abstractmethod
    async def put(self, lock_id: str, value: dict): ...

    @abc.abstractmethod
    async def delete(self, lock_id: str): ...

    @abc.abstractmethod
    def lock(self, lock_id: str, data: LockBody): ...

    @abc.abstractmethod
    def unlock(self): ...


class GitStateLockRepository(BaseStateLockRepository):
    def __init__(
        self,
        repo: pathlib.Path,
        ref: str = "main",
        state_file: str = "terraform.tfstate",
        sops_binary_path: pathlib.Path = "sops",
        key_path: pathlib.Path = "age_key.txt",
        sops_config_path: pathlib.Path = None,
    ):
        self.repo = repo
        self.ref = ref
        self.state_file = state_file
        self.sops_config_file = sops_config_path or self.repo / '.sops.yaml'
        print(self.sops_config_file)
        self.sops = Sops(
            sops_binary_path,
            self.repo,
            config=self.sops_config_file,
            env={
                "SOPS_AGE_KEY_FILE": str(key_path),
            },
        )

    def _git(self, command: str, *args):
        proc = subprocess.run(
            ["git", command, *args],
            cwd=self.repo,
            capture_output=True,
            text=True,
        )

        if proc.returncode != 0:
            raise Exception(f"Error running git command: {proc.stderr}")

        return proc.stdout

    async def get(self):
        self._cleanup_workspace()

        # pull latest changes
        self._git("pull", "origin", self.ref)

        # read state
        state_file = os.path.join(self.repo, self.state_file)
        try:
            with open(state_file, "r") as f:
                data = f.read()

        except FileNotFoundError:
            return None

        # decrypt data
        content = await self.sops.decrypt(state_file, data)
        return json.loads(content)

    async def put(self, lock_id: str, value: dict):
        await self._check_lock(lock_id)
        # lock is locked by me

        self._cleanup_workspace()
        # pull latest changes
        self._git("pull", "origin", self.ref)

        # save state
        state_file = os.path.join(self.repo, self.state_file)
        data = await self.sops.encrypt(state_file, json.dumps(value))
        with open(state_file, "w") as f:
            f.write(data)

        self._git("add", state_file)
        self._git("commit", "-m", f"Update state - id {lock_id}")
        self._git("push", "origin", self.ref)

    async def delete(self, lock_id: str):
        await self._check_lock(lock_id)
        # lock is locked by me

        self._cleanup_workspace()
        # pull latest changes
        self._git("pull", "origin", self.ref)

        # delete state
        state_file = os.path.join(self.repo, self.state_file)
        os.remove(state_file)

        self._git("add", state_file)
        self._git("commit", "-m", f"Delete state - id {lock_id}")
        self._git("push", "origin", self.ref)

    def _cleanup_workspace(self):
        self._git("reset", "--hard")
        self._git("checkout", self.ref)

    async def _check_lock(self, lock_id: str):
        self._cleanup_workspace()
        # delete lock branch if it exists
        with suppress(Exception):
            self._git("branch", "-D", f"locks/{self.state_file}")
        # pull latest changes
        self._git("fetch", "origin", "refs/heads/locks/*:refs/remotes/origin/locks/*")

        try:
            self._git("checkout", f"locks/{self.state_file}")

        except Exception:
            return None

        # read lock data
        lock_file = os.path.join(self.repo, "locks", f"{self.state_file}.lock")
        with open(lock_file, "r") as f:
            data = f.read()

        # decrypt data
        parsed = LockBody.model_validate_json(data)

        if parsed.ID != lock_id:
            raise LockingError(
                "Failed to lock state - someone else has already locked it",
                lock_id=lock_id,
            )

        return parsed

    def lock(self, lock_id: str, data: LockBody):
        self._cleanup_workspace()

        # delete lock branch if it exists
        with suppress(Exception):
            self._git("branch", "-D", f"locks/{self.state_file}")
        # pull latest changes
        self._git("pull", "origin", self.ref)

        # create a new locking branch
        self._git("checkout", "-b", f"locks/{self.state_file}")

        # make sure lock folder exists
        locks_dir = os.path.join(self.repo, "locks")
        os.makedirs(locks_dir, exist_ok=True)
        # write lock file
        lock_file = os.path.join(locks_dir, f"{self.state_file}.lock")
        with open(lock_file, "w") as f:
            f.write(data.model_dump_json())

        self._git("add", lock_file)
        self._git("commit", "-m", f"Locking state - id {lock_id}")
        try:
            self._git("push", "origin", f"locks/{self.state_file}")
        except Exception as e:
            raise LockingError(
                "Failed to push lock to the repository - assume someone else has locked it",
                lock_id=lock_id,
            ) from e

    def unlock(self):
        self._git("push", "origin", "--delete", f"locks/{self.state_file}")
