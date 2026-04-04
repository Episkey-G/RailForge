from pathlib import Path


def test_readme_mentions_npx_railforge_workflow() -> None:
    readme = Path("/Users/episkey/MyProjects/RailForge/RailForge/README.md").read_text(encoding="utf-8")

    assert "npx railforge-workflow" in readme
    assert "配置 MCP" in readme


def test_installer_docs_cover_ccg_mcp_parity() -> None:
    text = Path("/Users/episkey/MyProjects/RailForge/RailForge/docs/architecture/testing-matrix.md").read_text(
        encoding="utf-8"
    )

    assert "ace-tool" in text
    assert "fast-context" in text
    assert "ContextWeaver" in text
    assert "grok-search" in text
    assert "Context7" in text
    assert "Playwright" in text
