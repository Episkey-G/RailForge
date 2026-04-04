from __future__ import annotations

from pathlib import Path


class OpenSpecBridge:
    def __init__(self, workspace: Path) -> None:
        self.workspace = Path(workspace)
        self.root = self.workspace / "openspec"

    def ensure_root(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "changes").mkdir(parents=True, exist_ok=True)
        (self.root / "specs").mkdir(parents=True, exist_ok=True)
        return self.root

    def ensure_change(self, change_id: str) -> Path:
        self.ensure_root()
        path = self.root / "changes" / change_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_proposal(self, change_id: str, content: str) -> Path:
        path = self.ensure_change(change_id) / "proposal.md"
        path.write_text(content, encoding="utf-8")
        return path

    def write_design(self, change_id: str, content: str) -> Path:
        path = self.ensure_change(change_id) / "design.md"
        path.write_text(content, encoding="utf-8")
        return path

    def write_tasks(self, change_id: str, content: str) -> Path:
        path = self.ensure_change(change_id) / "tasks.md"
        path.write_text(content, encoding="utf-8")
        return path

    def write_spec(self, change_id: str, spec_name: str, content: str) -> Path:
        path = self.ensure_change(change_id) / "specs" / spec_name
        path.mkdir(parents=True, exist_ok=True)
        spec_path = path / "spec.md"
        spec_path.write_text(content, encoding="utf-8")
        return spec_path
