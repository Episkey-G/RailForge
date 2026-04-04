import re
from typing import List

from railforge.core.models import ProductSpec


def expand_request(project: str, request_text: str) -> ProductSpec:
    segments = [item.strip() for item in re.split(r"[。！？!?\.]+", request_text) if item.strip()]
    if not segments:
        segments = [request_text.strip() or "待补充需求"]
    summary = "；".join(segments)
    constraints = [
        "一次只处理一个 ready task",
        "仅在 contract 指定目录内写入",
        "完成标准必须机器可验证",
    ]
    return ProductSpec(
        title=project,
        summary=summary,
        acceptance_criteria=segments,
        constraints=constraints,
    )

