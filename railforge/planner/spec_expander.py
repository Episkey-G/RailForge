from railforge.core.models import ProductSpec
from railforge.planner.clarification import analyze_request


def expand_request(project: str, request_text: str) -> ProductSpec:
    return analyze_request(project=project, request_text=request_text, answers={}).spec
