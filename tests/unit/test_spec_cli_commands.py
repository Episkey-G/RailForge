from railforge.cli import build_parser


def test_cli_supports_spec_init_impl_and_review() -> None:
    parser = build_parser()

    assert parser.parse_args(["spec-init", "--workspace", "/tmp/demo"]).command == "spec-init"
    assert parser.parse_args(["spec-impl", "--workspace", "/tmp/demo"]).command == "spec-impl"
    assert parser.parse_args(["spec-review", "--workspace", "/tmp/demo"]).command == "spec-review"
