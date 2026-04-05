from __future__ import annotations

import sys
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_CODEX_FILES = [
    ".codex/config.toml",
    ".codex/hooks.json",
    ".codex/agents/lead-writer.toml",
    ".codex/agents/backend-specialist.toml",
    ".codex/agents/frontend-specialist.toml",
    ".codex/agents/backend-evaluator.toml",
    ".codex/agents/frontend-evaluator.toml",
]

REQUIRED_SKILL_ASSETS = [
    ".agents/skills/rf-spec-init/assets/phase-contract.yaml",
    ".agents/skills/rf-spec-research/assets/clarification-schema.json",
    ".agents/skills/rf-spec-plan/assets/planning-contract-template.yaml",
    ".agents/skills/rf-spec-impl/assets/contract-template.md",
    ".agents/skills/rf-spec-review/assets/review-rubric.md",
    ".agents/skills/rf-resume/assets/phase-contract.yaml",
    ".agents/skills/rf-status/assets/phase-contract.yaml",
]

LEGACY_TRUTH_DIRS = [
    ".railforge/product",
    ".railforge/planning",
    ".railforge/execution",
]

FORBIDDEN_RAILFORGE_PATTERNS = {
    "_heuristic_payload": "python heuristic clarification fallback must not return",
    "runtime/execution/tasks": "legacy runtime execution tree must not be a write target",
}


def main() -> int:
    errors: list[str] = []

    for relative in REQUIRED_CODEX_FILES + REQUIRED_SKILL_ASSETS:
        path = REPO_ROOT / relative
        if not path.exists():
            errors.append(f"missing required boundary asset: {relative}")

    for relative in LEGACY_TRUTH_DIRS:
        path = REPO_ROOT / relative
        if path.exists():
            errors.append(f"legacy truth directory must not exist in repo root: {relative}")

    if not (REPO_ROOT / "docs" / "product-specs" / "active").exists():
        errors.append("docs/product-specs/active is missing")
    if not (REPO_ROOT / "docs" / "exec-plans" / "active").exists():
        errors.append("docs/exec-plans/active is missing")
    if not (REPO_ROOT / "docs" / "quality" / "active").exists():
        errors.append("docs/quality/active is missing")

    commands_path = REPO_ROOT / "railforge" / "commands.py"
    if commands_path.exists():
        line_count = len(commands_path.read_text(encoding="utf-8").splitlines())
        if line_count > 100:
            errors.append(f"railforge/commands.py is too large for a thin facade: {line_count} lines")

    for pattern, message in FORBIDDEN_RAILFORGE_PATTERNS.items():
        result = subprocess.run(
            ["rg", "-n", pattern, "railforge", "--glob", "!railforge/artifacts/loaders.py"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        if lines:
            errors.append(f"{message}: {lines[0]}")

    if errors:
        for item in errors:
            print(item, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
