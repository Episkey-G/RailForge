import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from railforge.core.errors import ArtifactNotFoundError
from railforge.core.models import CheckpointRecord, RunMeta, TaskItem, WorkspaceLayout


class FileCheckpointStore:
    def __init__(self, layout: WorkspaceLayout) -> None:
        self.layout = layout

    def _atomic_write(self, path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=path.name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
            os.replace(tmp_path, path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def save(
        self,
        run_meta: RunMeta,
        backlog: Dict[str, Any],
        current_task: Optional[TaskItem],
        langgraph_ref: Optional[Dict[str, str]] = None,
    ) -> CheckpointRecord:
        sequence = run_meta.checkpoint_index + 1
        file_name = "%04d-%s.json" % (sequence, run_meta.state.value.lower())
        path = self.layout.checkpoints / file_name
        payload = {
            "sequence": sequence,
            "run_state": run_meta.to_dict(),
            "backlog": backlog,
            "current_task": current_task.to_dict() if current_task else None,
            "langgraph": langgraph_ref or {},
        }
        self._atomic_write(path, payload)
        return CheckpointRecord(sequence=sequence, state=run_meta.state, path=path, langgraph=langgraph_ref or {})

    def load_latest(self) -> Dict[str, Any]:
        files = sorted(self.layout.checkpoints.glob("*.json"))
        if not files:
            raise ArtifactNotFoundError(str(self.layout.checkpoints))
        return json.loads(files[-1].read_text(encoding="utf-8"))
