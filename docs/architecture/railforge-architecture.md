# RailForge Architecture

## Project Goal

RailForge is a spec-driven agent harness that uses a Codex CLI-first workflow.
The workflow is split into explicit stages so research, planning, execution, review, resume, and status checks stay separate.

## Workflow Model

1. `spec-research` collects context, constraints, and HITL questions.
2. `spec-plan` turns the research into an ordered implementation plan.
3. `execute` uses hosted Codex by default through the `prepare-execution / record-execution` handshake.
4. `review` checks the result against the plan and calls out gaps.
5. `resume` continues a blocked or paused workflow after human input.
6. `status` reports the current state without changing anything.

## Truth Layers

- `docs/architecture/` stores long-lived project documentation that belongs in version control.
- `.railforge/` stores runtime truth, including spec drafts, backlog artifacts, task execution output, approvals, and checkpoints.
- `.agents/skills/` stores workflow entrypoints for Codex CLI and remains part of the formal project repository.

## HITL Planning Stage

The human-in-the-loop boundary sits in `spec-research`.
That stage must identify unresolved assumptions, scope limits, and decisions that need human confirmation before execution starts.
If a question affects scope, risk, or architecture, it belongs in the research output instead of being guessed during execution.

## Package Boundaries

- The runtime package remains under `railforge/`.
- `railforge.codeagent` is the external runner subsystem for `Claude / Gemini` and Codex fallback.
- Hosted Codex is the default lead writer path and is coordinated by the skill layer, not by spawning `codex exec` as the primary path.
- Internal package layering stays explicit: `core`、`artifacts`、`orchestrator`、`planner`、`evaluator`、`execution`、`infra`。
- Runtime code must not write generated artifacts into `docs/`; generated output belongs under `.railforge/`.
