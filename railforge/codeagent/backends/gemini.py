from __future__ import annotations


def build_gemini_command(*, workspace: str, prompt: str, session_id: str | None = None) -> list[str]:
    command = ["gemini"]
    if session_id:
        command.extend(["--resume", session_id])
    command.extend(
        [
            "-p",
            prompt,
            "-o",
            "json",
            "-y",
            "--include-directories",
            workspace,
        ]
    )
    return command
