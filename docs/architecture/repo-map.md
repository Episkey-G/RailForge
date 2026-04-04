# RailForge Repo Map

## Top-Level Areas

| Path | Purpose |
| --- | --- |
| `railforge/` | Runtime package for the harness, adapters, planner, orchestrator, and evaluation logic. |
| `railforge/codeagent/` | External runner subsystem for `Claude / Gemini` and Codex fallback/headless execution. |
| `.agents/skills/` | Codex CLI-first workflow entrypoints for research, planning, execution, review, resume, and status. |
| `docs/architecture/` | Long-lived architecture notes and repository guidance. |
| `.railforge/` | Runtime truth layer generated per workspace run. |
| `tests/` | Unit and integration coverage for runtime behavior and workflow entrypoints. |
| `README.md` | Project overview and recommended operating flow. |

## Workflow Entry Points

| Skill | Command | Responsibility |
| --- | --- | --- |
| `rf-spec-research` | `python -m railforge spec-research` | Gather context, surface HITL questions, and define the problem. |
| `rf-spec-plan` | `python -m railforge spec-plan` | Turn approved research into an executable plan. |
| `rf-execute` | `python -m railforge prepare-execution` + `python -m railforge record-execution` | Use hosted Codex to implement the approved plan and hand the result back to the Python state machine. |
| `rf-review` | `python -m railforge review` | Review the delivered work against the spec and plan. |
| `rf-resume` | `python -m railforge resume` | Continue a paused or blocked workflow. |
| `rf-status` | `python -m railforge status` | Report the current workflow state. |

## Notes

- The formal repository keeps only source, tests, skills, and long-term documentation.
- Runtime-generated product specs, backlogs, approvals, and checkpoints live under `.railforge/`.
- Development-process plans and temporary design artifacts stay in the outer workspace, not in the formal repository.
