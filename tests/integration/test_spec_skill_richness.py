from pathlib import Path


ROOT = Path("/Users/episkey/MyProjects/RailForge/RailForge")


def _read_skill(name: str) -> str:
    return (ROOT / ".agents" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def test_spec_init_skill_has_guardrails_and_summary() -> None:
    text = _read_skill("rf-spec-init")
    assert "Core Philosophy" in text
    assert "Guardrails" in text
    assert "OpenSpec" in text
    assert "MCP" in text
    assert "Next Steps" in text
    assert "npx railforge-workflow doctor" in text
    assert "python -m railforge doctor" not in text
    assert "railforge spec-init --workspace <当前仓库路径>" in text


def test_spec_research_skill_enforces_constraints_and_boundary() -> None:
    text = _read_skill("rf-spec-research")
    assert "constraint" in text.lower() or "约束" in text
    assert "Guardrails" in text
    assert "OpenSpec proposal" in text or "proposal" in text
    assert "Do NOT proceed to planning or implementation" in text or "不要进入" in text


def test_spec_plan_skill_emphasizes_zero_decision_and_tasks() -> None:
    text = _read_skill("rf-spec-plan")
    assert "zero-decision" in text or "零决策" in text
    assert "ambigu" in text.lower() or "歧义" in text
    assert "tasks.md" in text or "task" in text.lower()


def test_spec_impl_skill_describes_hosted_codex_loop() -> None:
    text = _read_skill("rf-spec-impl")
    assert "Hosted Codex" in text
    assert "prepare-execution" in text
    assert "record-execution" in text
    assert "review" in text.lower()
    assert "repair" in text.lower() or "修复" in text


def test_spec_review_skill_has_dual_model_gate() -> None:
    text = _read_skill("rf-spec-review")
    assert "Claude" in text
    assert "Gemini" in text
    assert "Critical" in text or "严重" in text
    assert "Warning" in text or "警告" in text
    assert "Info" in text or "信息" in text
