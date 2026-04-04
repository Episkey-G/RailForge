from railforge.codeagent.backends.claude import build_claude_command
from railforge.codeagent.backends.codex import build_codex_command
from railforge.codeagent.backends.gemini import build_gemini_command


def test_codex_command_uses_exec_and_normalized_effort() -> None:
    command = build_codex_command(workspace="/tmp/demo", model="gpt-5.4", reasoning_effort="xhigh")

    assert command[:4] == ["codex", "exec", "--json", "-C"]
    assert "--skip-git-repo-check" in command
    assert 'model_reasoning_effort="high"' in " ".join(command)


def test_codex_command_forces_supported_effort_when_missing() -> None:
    command = build_codex_command(workspace="/tmp/demo")

    assert 'model_reasoning_effort="high"' in " ".join(command)


def test_claude_command_uses_print_and_json_output() -> None:
    command = build_claude_command(prompt="hello")

    assert command[:4] == ["claude", "-p", "--output-format", "json"]


def test_gemini_command_uses_headless_prompt_mode() -> None:
    command = build_gemini_command(workspace="/tmp/demo", prompt="hello")

    assert command[0] == "gemini"
    assert "-p" in command
    assert "-o" in command
    assert "--include-directories" in command
