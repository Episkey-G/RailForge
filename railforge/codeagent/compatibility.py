from __future__ import annotations

from typing import Optional


BACKEND_ALIASES = {
    "codex_cli": "codex",
    "claude_cli": "claude",
    "gemini_cli": "gemini",
}


def normalize_backend_name(backend: str) -> str:
    return BACKEND_ALIASES.get(backend, backend)


def normalize_reasoning_effort(backend: str, effort: Optional[str]) -> Optional[str]:
    backend = normalize_backend_name(backend)
    if backend != "codex":
        return effort
    if effort is None:
        return "high"
    if effort in {"xhigh", "max"}:
        return "high"
    return effort
