DEFAULT_TIMEOUTS = {
    "codex": 180,
    "claude": 120,
    "gemini": 90,
}


def timeout_for_backend(backend: str) -> int:
    return DEFAULT_TIMEOUTS[backend]
