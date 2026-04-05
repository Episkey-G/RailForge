from __future__ import annotations

import json
import re
from typing import Any

from railforge.adapters.base import AdapterResult, SpecialistAdapter
from railforge.integrations.codeagent import CodeagentWrapper
from railforge.providers.role_router import RoleRouter


class GeminiCliSpecialistAdapter(SpecialistAdapter):
    def __init__(
        self,
        delegate: Any = None,
        role_name: str = "frontend_specialist",
        role_router: RoleRouter | None = None,
        wrapper: CodeagentWrapper | None = None,
    ) -> None:
        self.delegate = delegate
        self.role_name = role_name
        self.role_router = role_router or RoleRouter()
        self.wrapper = wrapper or CodeagentWrapper()

    def _build_prompt(self, kwargs: dict[str, Any]) -> str:
        return (
            "你是 RailForge 的 %s（Gemini 路径）。\n"
            "请始终参与双模型审查，但你的侧重点固定为前端/UX/integration 视角，不直接改写无关模块。\n"
            "即使当前任务主要是后端任务，也要检查这些维度：错误信息是否会影响用户可见行为、接口/契约变化是否会影响前端集成、可维护性与一致性是否会给后续前端实现带来风险。\n"
            "如果前端维度没有阻塞项，请明确给出 passed，并在 summary 中说明“未发现前端/UX/integration 侧阻塞问题”；不要因为缺少纯 UI 代码就拒绝审查，也不要为了凑结论强行制造无关问题。\n\n"
            "请只输出 JSON，对象结构固定为：\n"
            '{"status":"passed|failed","summary":"...","findings":[{"severity":"critical|high|medium|low","source":"frontend","message":"...","evidence":"..."}],"details":{"failure_signature":"..."}}\n\n'
            "上下文：\n%s\n"
            % (self.role_name, json.dumps(kwargs, ensure_ascii=False, indent=2))
        )

    @staticmethod
    def _recover_structured_payload(result: AdapterResult) -> dict[str, Any]:
        structured = result.metadata.get("structured", {})
        if isinstance(structured, dict) and structured:
            return structured
        for candidate in (result.summary, result.metadata.get("stdout", "")):
            if not isinstance(candidate, str):
                continue
            match = re.search(r"```json\s*(\{.*?\})\s*```", candidate, re.S)
            if not match:
                continue
            try:
                payload = json.loads(match.group(1))
            except Exception:
                continue
            if isinstance(payload, dict):
                result.metadata["structured"] = payload
                return payload
        return {}

    def invoke(self, **kwargs: dict[str, Any]) -> AdapterResult:
        if self.delegate and hasattr(self.delegate, "invoke"):
            return self.delegate.invoke(**kwargs)
        task = kwargs.get("task", {})
        task_id = task.get("id", "unknown")
        role = kwargs.get("role", self.role_name)
        workspace = kwargs.get("workspace", ".")
        profile = self.role_router.profile_for_role(role)
        result = self.wrapper.run(
            role=role,
            backend=profile.backend,
            workspace=workspace,
            prompt=self._build_prompt(kwargs),
            payload={
                **kwargs,
                "role_policy": profile.to_dict(),
            },
        )
        structured = self._recover_structured_payload(result)
        if isinstance(structured, dict) and isinstance(structured.get("summary"), str) and structured.get("summary").strip():
            result.summary = structured["summary"].strip()
        result.summary = result.summary or "gemini review for %s" % task_id
        return result

    def review(self, task, qa_report, contract) -> AdapterResult:
        if self.delegate and hasattr(self.delegate, "review"):
            return self.delegate.review(task, qa_report, contract)
        return self.invoke(
            role=self.role_name,
            workspace=".",
            task=task.to_dict(),
            qa_report=qa_report.to_dict() if qa_report else None,
            contract=contract.to_dict(),
        )
