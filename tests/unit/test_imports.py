from railforge import __version__
from railforge.cli import build_parser


def test_package_exports_version() -> None:
    assert __version__ == "0.1.7"


def test_cli_parser_supports_run_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["run", "--workspace", "/tmp/demo", "--project", "demo", "--request", "add validation"])
    assert args.command == "run"
    assert args.project == "demo"
