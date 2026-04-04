from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from railforge import __version__
from railforge.codeagent.service import CodeagentService


def _read_payload(path: Optional[str]) -> Optional[dict]:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_prompt(args: argparse.Namespace) -> str:
    if getattr(args, "prompt", None):
        return args.prompt
    if getattr(args, "prompt_file", None):
        return Path(args.prompt_file).read_text(encoding="utf-8")
    return "请只返回 ok"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="railforge.codeagent")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("run", "resume"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--backend", required=True, choices=["codex", "claude", "gemini"])
        sub.add_argument("--role", required=True)
        sub.add_argument("--workspace", required=True)
        sub.add_argument("--prompt")
        sub.add_argument("--prompt-file")
        sub.add_argument("--payload-file")
        sub.add_argument("--model")
        sub.add_argument("--reasoning-effort")
        sub.add_argument("--timeout-seconds", type=int)
        sub.add_argument("--dry-run", action="store_true")
        if name == "resume":
            sub.add_argument("--session-id", required=True)

    probe = subparsers.add_parser("probe")
    probe.add_argument("--backend", required=True, choices=["codex", "claude", "gemini"])
    probe.add_argument("--workspace", required=True)
    probe.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = CodeagentService(dry_run=getattr(args, "dry_run", False))
    if args.command == "probe":
        result = service.probe(backend=args.backend, workspace=args.workspace)
    elif args.command == "resume":
        result = service.resume(
            backend=args.backend,
            role=args.role,
            workspace=args.workspace,
            session_id=args.session_id,
            prompt=_read_prompt(args),
            payload=_read_payload(args.payload_file),
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            timeout_seconds=args.timeout_seconds,
        )
    else:
        result = service.run(
            backend=args.backend,
            role=args.role,
            workspace=args.workspace,
            prompt=_read_prompt(args),
            payload=_read_payload(args.payload_file),
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            timeout_seconds=args.timeout_seconds,
        )
    print(json.dumps(result.to_dict(), ensure_ascii=False))
    return 0
