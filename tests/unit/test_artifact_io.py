from pathlib import Path

from railforge.artifacts.loaders import ArtifactLoader
from railforge.artifacts.store import ArtifactStore
from railforge.artifacts.writers import ArtifactWriter
from railforge.core.models import ProductSpec, WorkspaceLayout


def test_workspace_init_writes_default_configs(tmp_path: Path) -> None:
    layout = WorkspaceLayout(tmp_path)
    store = ArtifactStore(layout)

    store.init_workspace()

    policies = store.read_yaml(layout.rf / "policies.yaml")
    models = store.read_yaml(layout.rf / "models.yaml")

    assert policies["budgets"]["default_repair_budget"] >= 1
    assert "lead_writer" in models["roles"]


def test_loader_writer_roundtrip(tmp_path: Path) -> None:
    layout = WorkspaceLayout(tmp_path)
    layout.ensure()
    writer = ArtifactWriter(layout)
    loader = ArtifactLoader(layout)

    spec = ProductSpec(
        title="demo",
        summary="summary",
        acceptance_criteria=["a", "b"],
        constraints=["c"],
    )

    writer.write_product_spec(spec)
    loaded = loader.load_product_spec()

    assert loaded.title == "demo"
    assert loaded.acceptance_criteria == ["a", "b"]
