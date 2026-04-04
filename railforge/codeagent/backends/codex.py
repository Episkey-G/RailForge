from __future__ import annotations

from typing import Optional

from railforge.codeagent.compatibility import normalize_reasoning_effort


def build_codex_command(
    *,
    workspace: str,
    model: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
) -> list[str]:
    command = [
        "codex",
        "exec",
        "--json",
        "-C",
        workspace,
        "--skip-git-repo-check",
    ]
    if model:
        command.extend(["--model", model])
    normalized = normalize_reasoning_effort("codex", reasoning_effort)
    if normalized:
        command.extend(["-c", f'model_reasoning_effort="{normalized}"'])
    command.append("-")
    return command
