import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable

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

    def inspect_workspace(self, workspace: Path) -> Dict[str, Any]:
        if not self._is_git_repo(workspace):
            return {
                "available": False,
                "dirty": False,
                "head": None,
                "branch": None,
                "status": [],
                "reason": "not_a_git_repo",
            }

        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
        )
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
        )
        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
        )
        lines = [line for line in status.stdout.splitlines() if line.strip()]
        return {
            "available": True,
            "dirty": bool(lines),
            "head": head.stdout.strip() or None,
            "branch": branch.stdout.strip() or None,
            "status": lines,
        }

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
