from pathlib import Path


ROOT = Path("/Users/episkey/MyProjects/RailForge/RailForge")
ALLOWED_DIRECT_LOADER_USERS = {
    ROOT / "railforge" / "workflow" / "assets.py",
    ROOT / "railforge" / "workflow" / "__init__.py",
}


def test_skill_asset_loading_is_centralized_in_workflow_assets_module() -> None:
    offenders: list[str] = []
    for path in sorted((ROOT / "railforge").rglob("*.py")):
        if path in ALLOWED_DIRECT_LOADER_USERS:
            continue
        text = path.read_text(encoding="utf-8")
        if "load_skill_yaml(" in text or "load_skill_text(" in text or "load_skill_json(" in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_phase_contract_asset_paths_are_not_hard_coded_outside_authority_layer() -> None:
    offenders: list[str] = []
    forbidden_tokens = [
        "phase-contract.yaml",
        "planning-contract-template.yaml",
        "review-rubric.md",
    ]
    for path in sorted((ROOT / "railforge").rglob("*.py")):
        if path == ROOT / "railforge" / "workflow" / "assets.py":
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden_tokens):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []
