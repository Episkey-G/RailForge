SUPPORTED_RESUME_BACKENDS = {"claude", "gemini"}


def backend_supports_resume(backend: str) -> bool:
    return backend in SUPPORTED_RESUME_BACKENDS
