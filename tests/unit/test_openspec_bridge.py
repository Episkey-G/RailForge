from pathlib import Path

from railforge.openspec_bridge import OpenSpecBridge


def test_openspec_bridge_writes_design_and_tasks(tmp_path: Path) -> None:
    bridge = OpenSpecBridge(tmp_path)
    change_dir = bridge.ensure_change("user-auth")

    bridge.write_design("user-auth", "# design")
    bridge.write_tasks("user-auth", "- [ ] task")
    bridge.write_spec("user-auth", "harness-core", "# spec")

    assert (change_dir / "design.md").exists()
    assert (change_dir / "tasks.md").exists()
    assert (change_dir / "specs" / "harness-core" / "spec.md").exists()
