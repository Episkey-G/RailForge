from railforge.workflow.assets import WorkflowAssetResolver


def test_workflow_asset_resolver_loads_phase_contracts_for_all_primary_phases() -> None:
    resolver = WorkflowAssetResolver()

    for phase in [
        "spec-init",
        "spec-research",
        "spec-plan",
        "spec-impl",
        "spec-review",
        "resume",
        "status",
    ]:
        contract = resolver.load_phase_contract(phase)
        assert contract["phase"] == phase
        assert contract["required_inputs"]
        assert contract["expected_outputs"]
        assert "allowed_actions" in contract
        assert "disallowed_actions" in contract


def test_workflow_asset_resolver_exposes_runtime_authority_inputs() -> None:
    resolver = WorkflowAssetResolver()

    planning_template = resolver.load_planning_contract_template()
    assert planning_template["approval"]["required"] is True

    rubric = resolver.load_review_rubric()
    assert "Deterministic First" in rubric

    references = resolver.load_phase_references("spec-plan")
    assert "phase-boundary.md" in references
    assert "contract-rules.md" in references


def test_workflow_asset_resolver_loads_clarification_bundle() -> None:
    resolver = WorkflowAssetResolver()

    research_assets = resolver.load_clarification_assets("research")
    plan_assets = resolver.load_clarification_assets("planning")

    assert research_assets.prompt_contract
    assert research_assets.schema
    assert research_assets.phase_contract["phase"] == "spec-research"
    assert "question" in research_assets.question_template.lower()

    assert plan_assets.prompt_contract
    assert plan_assets.schema
    assert plan_assets.phase_contract["phase"] == "spec-plan"
    assert "question" in plan_assets.question_template.lower()
