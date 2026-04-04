from railforge.cli import build_parser


def test_cli_supports_prepare_and_record_execution() -> None:
    parser = build_parser()

    assert parser.parse_args(["prepare-execution", "--workspace", "/tmp/demo"]).command == "prepare-execution"
    assert (
        parser.parse_args(["record-execution", "--workspace", "/tmp/demo", "--file", "/tmp/result.json"]).command
        == "record-execution"
    )
