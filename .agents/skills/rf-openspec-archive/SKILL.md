---
name: rf-openspec-archive
description: Bridge a completed RailForge change into the OpenSpec archive lifecycle.
---

# RF OpenSpec Archive

Use this skill when RailForge has already produced an approved `final_review.json` and the change should move into OpenSpec archival.

- Bridge target: `openspec-archive-change`
- Typical timing: after `rf-spec-review` and the change-level final gate are both green
- Expected output: archive the OpenSpec change and keep release notes in sync
