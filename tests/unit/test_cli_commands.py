from railforge.cli import build_parser


def test_cli_supports_codex_first_workflow_commands() -> None:
    parser = build_parser()

    args = parser.parse_args(["spec-research", "--workspace", "/tmp/demo", "--request", "实现 JWT 登录"])
    assert args.command == "spec-research"

    args = parser.parse_args(["spec-plan", "--workspace", "/tmp/demo"])
    assert args.command == "spec-plan"

    args = parser.parse_args(["approve", "--workspace", "/tmp/demo", "--target", "spec"])
    assert args.command == "approve"
    assert args.target == "spec"

    args = parser.parse_args(["answer", "--workspace", "/tmp/demo", "--file", "/tmp/demo/answers.yaml"])
    assert args.command == "answer"


def test_cli_supports_status_and_execute_commands() -> None:
    parser = build_parser()

    args = parser.parse_args(["status", "--workspace", "/tmp/demo"])
    assert args.command == "status"

    args = parser.parse_args(["execute", "--workspace", "/tmp/demo"])
    assert args.command == "execute"
