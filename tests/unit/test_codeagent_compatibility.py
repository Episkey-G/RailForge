from railforge.codeagent.compatibility import normalize_reasoning_effort


def test_normalize_reasoning_effort_downgrades_unsupported_codex_level() -> None:
    assert normalize_reasoning_effort("codex", "xhigh") == "high"
    assert normalize_reasoning_effort("codex", "max") == "high"
    assert normalize_reasoning_effort("codex", "medium") == "medium"
    assert normalize_reasoning_effort("claude", "xhigh") == "xhigh"
