from railforge.providers.claude_cli import ClaudeCliSpecialistAdapter
from railforge.providers.gemini_cli import GeminiCliSpecialistAdapter


def test_gemini_review_prompt_keeps_dual_review_and_frontend_focus() -> None:
    prompt = GeminiCliSpecialistAdapter()._build_prompt(
        {
            "role": "frontend_specialist",
            "task": {"id": "T-001", "title": "实现后端能力：过去日期校验"},
            "contract": {"allowed_paths": ["backend/", "tests/"]},
        }
    )

    assert "始终参与双模型审查" in prompt
    assert "前端/UX/integration 视角" in prompt
    assert "未发现前端/UX/integration 侧阻塞问题" in prompt


def test_claude_review_prompt_calls_out_complementary_focus() -> None:
    prompt = ClaudeCliSpecialistAdapter()._build_prompt(
        {
            "role": "backend_specialist",
            "task": {"id": "T-001", "title": "实现后端能力：过去日期校验"},
            "contract": {"allowed_paths": ["backend/", "tests/"]},
        }
    )

    assert "始终参与双模型审查" in prompt
    assert "correctness" in prompt
    assert "Gemini 的前端/UX/integration 视角互补" in prompt
