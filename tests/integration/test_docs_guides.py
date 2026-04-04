from pathlib import Path


ROOT = Path("/Users/episkey/MyProjects/RailForge/RailForge")


def test_commands_guide_exists_and_lists_spec_workflow() -> None:
    text = (ROOT / "docs" / "guide" / "commands.md").read_text(encoding="utf-8")

    assert "/rf:spec-init" in text
    assert "/rf:spec-research" in text
    assert "/rf:spec-plan" in text
    assert "/rf:spec-impl" in text
    assert "/rf:spec-review" in text
    assert "/rf:openspec-apply" in text
    assert "/rf:openspec-archive" in text
    assert "final_review.json" in text


def test_faq_guide_exists_and_covers_common_questions() -> None:
    text = (ROOT / "docs" / "guide" / "faq.md").read_text(encoding="utf-8")

    assert "codeagent-wrapper: command not found" in text
    assert "如何让 codeagent 无需同意即可运行" in text
    assert "Codex 任务卡住" in text
    assert "Claude Code 任务超时" in text
    assert "OpenSpec CLI 装不上" in text
