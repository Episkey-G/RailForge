---
name: rf-openspec-apply
description: Bridge an approved RailForge change into the OpenSpec apply lifecycle.
---

# RF OpenSpec Apply

Use this skill when a RailForge change has finished planning or review and should continue through the OpenSpec task application flow.

- Bridge target: `openspec-apply-change`
- Typical timing: after `rf-spec-review` identifies the next implementation pass
- Expected output: OpenSpec tasks continue moving instead of stopping at the RailForge runtime boundary
