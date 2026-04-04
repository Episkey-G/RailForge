---
name: rf-resume
description: Codex CLI-first skill for resuming a blocked or paused RailForge workflow.
---

# RF Resume

Use this skill when a workflow is blocked, paused, or waiting on human input.

- Entry point: `python -m railforge resume`
- If the blocked reason is `hosted_execution_required`, prefer finishing the hosted Codex flow through `record-execution` before using plain `resume`.
- Rehydrate the latest state before continuing.
- Capture the human decision or override that unblocks the workflow.
- Continue from the last validated checkpoint instead of restarting.
- Keep the resume note short and explicit so the next step is obvious.
