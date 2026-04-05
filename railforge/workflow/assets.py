from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / ".agents" / "skills"

PHASE_SKILL_MAP = {
    "spec-init": "rf-spec-init",
    "spec-research": "rf-spec-research",
    "spec-plan": "rf-spec-plan",
    "spec-impl": "rf-spec-impl",
    "spec-review": "rf-spec-review",
    "resume": "rf-resume",
    "status": "rf-status",
}

CLARIFICATION_PHASE_SKILL_MAP = {
    "research": "rf-spec-research",
    "planning": "rf-spec-plan",
}


def _asset_path(skill_name: str, *parts: str) -> Path:
    return SKILLS_ROOT / skill_name / Path(*parts)


def load_skill_text(skill_name: str, *parts: str) -> str:
    path = _asset_path(skill_name, *parts)
    return path.read_text(encoding="utf-8")


def load_skill_yaml(skill_name: str, *parts: str) -> Dict[str, Any]:
    payload = yaml.safe_load(load_skill_text(skill_name, *parts))
    return payload or {}


def load_skill_json(skill_name: str, *parts: str) -> Dict[str, Any]:
    return json.loads(load_skill_text(skill_name, *parts))


@dataclass(frozen=True)
class ClarificationAssets:
    prompt_contract: Dict[str, Any]
    schema: Dict[str, Any]
    phase_contract: Dict[str, Any]
    boundary_reference: str
    question_template: str


class WorkflowAssetResolver:
    def __init__(self, skills_root: Path = SKILLS_ROOT) -> None:
        self.skills_root = skills_root

    def skill_for_phase(self, phase: str) -> str:
        return PHASE_SKILL_MAP.get(phase, "rf-status")

    def skill_for_clarification_phase(self, phase: str) -> str:
        return CLARIFICATION_PHASE_SKILL_MAP.get(phase, "rf-spec-plan")

    def load_phase_contract(self, phase: str) -> Dict[str, Any]:
        return self._load_optional_yaml(self.skill_for_phase(phase), "assets", "phase-contract.yaml")

    def load_phase_references(self, phase: str) -> Dict[str, str]:
        skill_name = self.skill_for_phase(phase)
        references_dir = self.skills_root / skill_name / "references"
        if not references_dir.exists():
            return {}
        payload: Dict[str, str] = {}
        for path in sorted(references_dir.glob("*.md")):
            payload[path.name] = load_skill_text(skill_name, "references", path.name)
        return payload

    def load_planning_contract_template(self) -> Dict[str, Any]:
        return self._load_optional_yaml("rf-spec-plan", "assets", "planning-contract-template.yaml")

    def load_review_rubric(self) -> str:
        return self._load_optional_text("rf-spec-review", "assets", "review-rubric.md")

    def load_clarification_assets(self, phase: str) -> ClarificationAssets:
        skill_name = self.skill_for_clarification_phase(phase)
        return ClarificationAssets(
            prompt_contract=self._load_optional_yaml(skill_name, "assets", "clarification-prompt.yaml"),
            schema=self._load_optional_json(skill_name, "assets", "clarification-schema.json"),
            phase_contract=self._load_optional_yaml(skill_name, "assets", "phase-contract.yaml"),
            boundary_reference=self._load_optional_text(skill_name, "references", "phase-boundary.md"),
            question_template=self._load_optional_text(skill_name, "references", "question-template.md"),
        )

    def _load_optional_text(self, skill_name: str, *parts: str) -> str:
        try:
            return (self.skills_root / skill_name / Path(*parts)).read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    def _load_optional_yaml(self, skill_name: str, *parts: str) -> Dict[str, Any]:
        payload = yaml.safe_load(self._load_optional_text(skill_name, *parts))
        return payload or {}

    def _load_optional_json(self, skill_name: str, *parts: str) -> Dict[str, Any]:
        text = self._load_optional_text(skill_name, *parts)
        if not text:
            return {}
        return json.loads(text)
