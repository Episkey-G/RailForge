from railforge.adapters.codeagent_wrapper import CodeagentWrapper


def test_build_command_uses_native_wrapper_entry() -> None:
    wrapper = CodeagentWrapper()
    command = wrapper.build_command("codex", "/tmp/railforge")

    assert command[:4] == ["python", "-m", "railforge.codeagent", "run"]
    assert "--backend" in command
    assert "codex" in command
    assert "--workspace" in command
    assert "/tmp/railforge" in command


def test_build_invocation_serializes_payload() -> None:
    wrapper = CodeagentWrapper()

    invocation = wrapper.build_invocation(
        role="lead_writer",
        backend="codex",
        workspace="/tmp/railforge",
        payload={"task": {"id": "T-001"}},
    )

    assert invocation.to_dict() == {
        "role": "lead_writer",
        "backend": "codex",
        "workspace": "/tmp/railforge",
        "command": [
            "python",
            "-m",
            "railforge.codeagent",
            "run",
            "--backend",
            "codex",
            "--workspace",
            "/tmp/railforge",
        ],
        "payload": {"task": {"id": "T-001"}},
    }
