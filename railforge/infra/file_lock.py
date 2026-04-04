from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from railforge.core.errors import RailForgeError


class WorkspaceLockError(RailForgeError):
    """Raised when the workspace lock cannot be acquired."""


class WorkspaceLock:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._owner = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        owner = uuid4().hex
        try:
            fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise WorkspaceLockError("workspace lock already held: %s" % self.path) from exc

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(owner)
        except Exception:
            if self.path.exists():
                self.path.unlink()
            raise
        self._owner = owner

    def release(self) -> None:
        if self._owner is None:
            return
        if self.path.exists():
            current = self.path.read_text(encoding="utf-8")
            if current == self._owner:
                self.path.unlink()
        self._owner = None

    def __enter__(self) -> "WorkspaceLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()
