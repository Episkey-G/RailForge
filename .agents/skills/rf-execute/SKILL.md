---
name: rf-execute
description: Codex CLI-first skill for implementing an approved RailForge plan.
---

# RF Execute

Use this skill when the plan is approved and implementation should start.

- Hosted Codex path:
  - Run `railforge prepare-execution --workspace <workspace> --profile real`
  - Read the returned JSON context
  - In the current hosted Codex session, implement only the approved scope
  - Persist an execution result JSON with `task_id`, `summary`, and `changed_files`
  - Run `railforge record-execution --workspace <workspace> --profile real --file <result.json>`
- `prepare-execution` and `record-execution` are the protocol boundary between the Python state machine and hosted Codex.
- Keep changes narrow and aligned with the existing codebase structure.
- Validate the change with the smallest useful test set before handing off.
- Report blockers clearly so `rf-review` and `rf-resume` can continue from the right state.
- This skill assumes hosted Codex is the default lead writer path.
