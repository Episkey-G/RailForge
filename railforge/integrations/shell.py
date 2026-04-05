import subprocess
from pathlib import Path


class LocalShellAdapter:
    def run(self, workspace: Path, commands: list[str]) -> list[dict[str, str]]:
        results = []
        for command in commands:
            completed = subprocess.run(
                command,
                cwd=str(workspace),
                capture_output=True,
                shell=True,
                text=True,
            )
            results.append(
                {
                    "command": command,
                    "status": "passed" if completed.returncode == 0 else "failed",
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                }
            )
        return results
