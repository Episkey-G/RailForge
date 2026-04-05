from pathlib import Path

from railforge.artifacts.store import ArtifactStore
from railforge.core.models import ProductSpec, WorkspaceLayout


def test_truth_layer_bootstraps_docs_and_runtime_paths(tmp_path: Path) -> None:
    layout = WorkspaceLayout(tmp_path)
    store = ArtifactStore(layout)

    store.init_workspace()

    assert layout.runtime == tmp_path / ".railforge" / "runtime"
    assert layout.product_dir == tmp_path / "docs" / "product-specs" / "active"
    assert layout.planning_dir == tmp_path / "docs" / "exec-plans" / "active"
    assert layout.execution_dir == tmp_path / ".railforge" / "runtime" / "execution"
    assert layout.runtime.exists()
    assert layout.product_dir.exists()
    assert layout.planning_dir.exists()
    assert layout.execution_dir.exists()
    assert layout.models_path.exists()
    assert layout.policies_path.exists()


def test_truth_layer_roundtrips_planning_artifacts(tmp_path: Path) -> None:
    layout = WorkspaceLayout(tmp_path)
    store = ArtifactStore(layout)
    store.init_workspace()
    spec = ProductSpec(
        title="todo-app",
        summary="summary",
        acceptance_criteria=["A"],
        constraints=["C"],
        assumptions=["assumption"],
        open_questions=["请确认时区"],
        decision_points=["时区规则"],
        status="draft",
        source_request="原始需求",
    )

    store.save_product_spec(spec, draft=True)
    store.save_questions({"questions": [{"id": "Q-001", "prompt": "请确认时区"}]})
    store.save_answers({"answers": {"Q-001": "UTC"}})
    store.save_decisions({"decisions": [{"id": "D-001", "topic": "时区规则"}]})

    assert store.load_product_spec(draft=True).open_questions == ["请确认时区"]
    assert store.load_questions()["questions"][0]["id"] == "Q-001"
    assert store.load_answers()["answers"]["Q-001"] == "UTC"
    assert store.load_decisions()["decisions"][0]["topic"] == "时区规则"
