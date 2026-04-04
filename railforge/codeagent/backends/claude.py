from __future__ import annotations


def build_claude_command(*, prompt: str, session_id: str | None = None) -> list[str]:
    command = ["claude", "-p", "--output-format", "json"]
    if session_id:
        command.extend(["-r", session_id])
    command.append(prompt)
    return command
