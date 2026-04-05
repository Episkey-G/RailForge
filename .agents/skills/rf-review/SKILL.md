---
name: rf-review
description: Codex CLI-first skill for reviewing RailForge changes against the plan and spec.
---

# RF Review

Use this skill after execution to verify the result against the approved plan.

- Entry point: `railforge review`
- Compare the delivered change with the research notes and plan.
- Review is driven by the Python review gate and should include both Claude and Gemini outputs when they are available.
- Call out regressions, missing tests, and any scope drift.
- Prefer concrete findings over generic approval language.
- Use the review to decide whether `rf-resume` or another execution pass is needed.
