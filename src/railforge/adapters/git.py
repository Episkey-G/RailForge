import subprocess
from pathlib import Path
from typing import Iterable

from railforge.core.models import CommitGateResult


class DryRunGitAdapter:
    def __init__(self, allow_real_commits: bool = False) -> None:
        self.allow_real_commits = allow_real_commits

    def _is_git_repo(self, workspace: Path) -> bool:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def create_commit(self, workspace: Path, message: str, files: Iterable[str]) -> CommitGateResult:
        tracked = list(files)
        if not self._is_git_repo(workspace) or not self.allow_real_commits:
            return CommitGateResult(
                passed=True,
                message=message,
                dry_run=True,
                commit_hash=None,
                details={"reason": "git_unavailable_or_dry_run", "files": tracked},
            )

        add_result = subprocess.run(["git", "add"] + tracked, cwd=str(workspace), capture_output=True, text=True)
        if add_result.returncode != 0:
            return CommitGateResult(
                passed=False,
                message=message,
                dry_run=False,
                commit_hash=None,
                details={"stderr": add_result.stderr},
            )

        commit_result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=str(workspace),
            capture_output=True,
            text=True,
        )
        if commit_result.returncode != 0:
            return CommitGateResult(
                passed=False,
                message=message,
                dry_run=False,
                commit_hash=None,
                details={"stderr": commit_result.stderr},
            )

        sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
        )
        return CommitGateResult(
            passed=True,
            message=message,
            dry_run=False,
            commit_hash=sha_result.stdout.strip() or None,
            details={"files": tracked},
        )

