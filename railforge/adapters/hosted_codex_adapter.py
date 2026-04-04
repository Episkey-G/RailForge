from __future__ import annotations

import json

from railforge.adapters.base import LeadWriterAdapter
from railforge.core.models import AdapterResult


class HostedCodexAdapter(LeadWriterAdapter):
    def implement(self, layout, task, contract, run_meta) -> AdapterResult:
        prompt = (
            "你是 RailForge 的 lead writer（Hosted Codex）。\n"
            "严格遵守 contract 边界，只在允许目录内修改。\n\n"
            "上下文：\n"
            "%s\n"
            % json.dumps(
                {
                    "role": "lead_writer",
                    "workspace": str(layout.root),
                    "task": task.to_dict(),
                    "contract": contract.to_dict(),
                    "run_meta": run_meta.to_dict(),
                    "writable_paths": list(contract.allowed_paths)
                    + [str(layout.task_dir(task.id).relative_to(layout.root)) + "/"],
                },
                ensure_ascii=False,
                indent=2,
            )
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
            },
        )
