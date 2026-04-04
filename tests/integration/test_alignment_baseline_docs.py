from pathlib import Path


ROOT = Path("/Users/episkey/MyProjects/RailForge/RailForge")


def test_ccg_alignment_baseline_doc_covers_required_surfaces() -> None:
    text = (ROOT / "docs" / "architecture" / "ccg-alignment-baseline.md").read_text(encoding="utf-8")

    assert "安装器" in text
    assert "skills" in text
    assert "工作流入口" in text
    assert "MCP 分组" in text
    assert "运行时闭环" in text
    assert "固定 backlog" in text
    assert "spec-review" in text
    assert "langgraph_bridge.py" in text
    assert "AGENTS.md" in text


def test_persistence_recovery_baseline_doc_covers_truth_layers_and_recovery_rules() -> None:
    text = (ROOT / "docs" / "architecture" / "persistence-recovery-baseline.md").read_text(encoding="utf-8")

    assert "文件 + git 为业务真源" in text
    assert "system of record" in text
    assert "LangGraph" in text
    assert "checkpoint layer" in text
    assert "BLOCKED" in text
    assert "FAILED" in text
    assert "恢复" in text
