---
name: rf-spec-plan
description: Use when research is approved and the team must turn constraints into a zero-decision executable plan with tasks, contracts, and explicit ambiguity elimination.
---

# RF Spec Plan

## Core Philosophy

- `spec-plan` 的目标是消除所有实现阶段的决策点。
- 如果实现时还需要拍脑袋，说明计划阶段失败。
- 每个 requirement 都应该落成 task、contract、verification 或明确阻塞。

## Guardrails

- 不要带着关键歧义进入 `spec-impl`。
- 必须把 OpenSpec 的 design / tasks / spec 工件写完整。
- 必须把 `.railforge/planning/*` 和 task contract 落盘。
- 如果约束还不够清晰，返回 `spec-research` 或人工确认。

## Steps

1. 运行 `railforge spec-plan`
2. 审核 proposal 和 research 结果
3. 做零决策规划：
   - 技术选择
   - 任务拆分
   - 依赖顺序
   - contract
   - verification
4. 写入 OpenSpec：
   - `design.md`
   - `tasks.md`
   - `spec.md`
5. 写入 `.railforge/planning/*`

## Success Criteria

- OpenSpec 工件齐全
- backlog 可执行
- task contract 已生成
- 关键歧义被消除
- 下一步可以直接进入 `rf-spec-impl`
