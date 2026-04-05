from __future__ import annotations

import json

from railforge.adapters.base import LeadWriterAdapter
from railforge.core.models import AdapterResult


class HostedCodexAdapter(LeadWriterAdapter):
    def implement(self, layout, task, contract, run_meta) -> AdapterResult:
        task_root = str(layout.task_dir(task.id).relative_to(layout.root)) + "/"
        payload = {
            "role": "lead_writer",
            "workspace": str(layout.root),
            "task": task.to_dict(),
            "contract": contract.to_dict(),
            "run_meta": run_meta.to_dict(),
            "writable_paths": list(contract.allowed_paths) + [task_root],
            "task_context": list(contract.task_context),
            "writeback": dict(contract.writeback_requirements),
            "roles": dict(contract.role_boundaries),
            "artifacts": {
                "task_dir": task_root,
                "contract": str((layout.task_dir(task.id) / "contract.yaml").relative_to(layout.root)),
                "reviews_dir": str(layout.task_reviews_dir(task.id).relative_to(layout.root)) + "/",
                "proposals_dir": str(layout.task_proposals_dir(task.id).relative_to(layout.root)) + "/",
                "traces_dir": str(layout.task_traces_dir(task.id).relative_to(layout.root)) + "/",
            },
        }
        prompt = (
            "你是 RailForge 的 lead writer（Hosted Codex）。\n"
            "严格遵守 contract 边界，只在允许目录内修改。\n\n"
            "上下文：\n"
            "%s\n"
            % json.dumps(payload, ensure_ascii=False, indent=2)
        )
        return AdapterResult(
            success=False,
            summary="hosted Codex execution requires prepare/record handshake",
            metadata={
                "mode": "hosted_codex",
                "status": "pending_hosted_execution",
                "task_id": task.id,
                "workspace": str(layout.root),
                "prompt": prompt,
                "task": task.to_dict(),
                "contract": contract.to_dict(),
                "allowed_paths": list(contract.allowed_paths),
                "verification": list(contract.verification),
                "task_context": list(contract.task_context),
                "writeback": dict(contract.writeback_requirements),
                "roles": dict(contract.role_boundaries),
                "artifacts": payload["artifacts"],
            },
        )
