from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from railforge.artifacts.store import ArtifactStore
from railforge.context.assembler import ContextAssembler
from railforge.core.errors import ArtifactNotFoundError
from railforge.core.models import WorkspaceLayout


def build_phase_context(
    workspace: Path,
    *,
    phase: str,
    run_meta: Optional[dict[str, Any]] = None,
    task_id: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    layout = WorkspaceLayout(workspace)
    store = ArtifactStore(layout)
    assembler = ContextAssembler(layout, store)
    meta = None
    if run_meta:
        try:
            from railforge.core.models import RunMeta

            meta = RunMeta.from_dict(run_meta)
        except Exception:
            meta = None
    return assembler.build(phase=phase, run_meta=meta, task_id=task_id, extra=extra)


def load_run_state(workspace: Path) -> dict[str, Any]:
    store = ArtifactStore(WorkspaceLayout(workspace))
    try:
        return store.load_run_state().to_dict()
    except ArtifactNotFoundError:
        return {"state": "BOOTSTRAP", "workspace": str(workspace)}
