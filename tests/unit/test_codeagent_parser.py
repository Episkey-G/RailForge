from railforge.codeagent.parser import parse_agent_output


def test_parse_agent_output_extracts_session_id_and_fenced_json() -> None:
    parsed = parse_agent_output(
        stdout='```json\n{"status":"passed","summary":"ok"}\n```',
        stderr="SESSION_ID: abc-123",
    )

    assert parsed.session_id == "abc-123"
    assert parsed.structured["status"] == "passed"
    assert parsed.summary == '{"status":"passed","summary":"ok"}'


def test_parse_agent_output_parses_plain_json_object() -> None:
    parsed = parse_agent_output(
        stdout='{"session_id":"sess-1","response":"ok"}',
        stderr="",
    )

    assert parsed.session_id == "sess-1"
    assert parsed.structured["response"] == "ok"


def test_parse_agent_output_extracts_json_prefix_with_trailing_logs() -> None:
    parsed = parse_agent_output(
        stdout='{"session_id":"sess-2","response":"ok"}Created execution plan for SessionEnd',
        stderr="",
    )

    assert parsed.session_id == "sess-2"
    assert parsed.structured["response"] == "ok"


def test_parse_agent_output_summarizes_codex_jsonl_events() -> None:
    parsed = parse_agent_output(
        stdout=(
            '{"type":"thread.started","thread_id":"thread-1"}\n'
            '{"type":"item.completed","item":{"type":"agent_message","text":"ok"}}\n'
            '{"type":"turn.completed"}\n'
        ),
        stderr="",
    )

    assert parsed.session_id == "thread-1"
    assert parsed.summary == "ok"
    assert parsed.structured["events"][0]["type"] == "thread.started"
