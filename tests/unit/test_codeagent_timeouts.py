from railforge.codeagent.timeouts import timeout_for_backend


def test_timeout_for_backend_uses_backend_specific_defaults() -> None:
    assert timeout_for_backend("codex") == 180
    assert timeout_for_backend("claude") == 120
    assert timeout_for_backend("gemini") == 90
