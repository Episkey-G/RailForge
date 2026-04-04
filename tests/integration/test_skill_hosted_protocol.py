from pathlib import Path


def test_rf_execute_skill_references_prepare_and_record_execution() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    text = (repo_root / ".agents" / "skills" / "rf-execute" / "SKILL.md").read_text(encoding="utf-8")

    assert "prepare-execution" in text
    assert "record-execution" in text
    assert "hosted Codex" in text


def test_rf_review_skill_calls_python_review_gate() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    text = (repo_root / ".agents" / "skills" / "rf-review" / "SKILL.md").read_text(encoding="utf-8")

    assert "python -m railforge review" in text
    assert "Claude" in text
    assert "Gemini" in text
