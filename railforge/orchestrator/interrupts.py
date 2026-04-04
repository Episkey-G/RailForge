from __future__ import annotations

from typing import Any, Dict

from railforge.artifacts.loaders import ArtifactLoader
from railforge.artifacts.writers import ArtifactWriter
from railforge.core.models import WorkspaceLayout


class InterruptManager:
    def __init__(self, layout: WorkspaceLayout) -> None:
        self.layout = layout
        self.loader = ArtifactLoader(layout)
        self.writer = ArtifactWriter(layout)

    def record_blocked(
        self,
        task_id: str,
        reason: str,
        resume_from_state: str,
        note: str,
    ) -> Dict[str, Any]:
        self.layout.ensure(task_id)
        return self.writer.write_blocked_interrupt(
            task_id=task_id,
            reason=reason,
            resume_from_state=resume_from_state,
            note=note,
        )

    def load_blocked(self) -> Dict[str, Any]:
        return self.loader.load_blocked_interrupt()

    def record_unblock(self, reason: str, note: str) -> None:
        self.layout.ensure()
        self.writer.write_unblock_decision(reason=reason, note=note)

    def load_unblock_decision(self) -> Dict[str, Any]:
        return self.loader.load_unblock_decision()
