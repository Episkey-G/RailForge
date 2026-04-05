---
name: rf-spec-impl
description: Use when spec planning is approved and the full implementation loop should run through Hosted Codex, dual-model review, repair, and completion gates.
---

# RF Spec Impl

## Core Philosophy

- `spec-impl` 是按批准计划进行机械执行，而不是重新做设计。
- Hosted Codex 负责主写作，Claude/Gemini 负责外部 review / evaluator。
- 所有实现都必须回到 Python 状态机，由它决定是否进入下一 task、repair 或 blocked。

## Guardrails

- 不要越过 `tasks.md` 和 contract scope。
- Hosted Codex 的结果必须通过 `record-execution` 回写，不能只留在会话里。
- 不要跳过 review、repair 和 blocked 语义。
- 低层 `prepare-execution / record-execution` 是内部协议，不是主要用户心智。

## Hosted Codex Loop

1. 运行 `railforge spec-impl`
2. 由 workflow 进入 Hosted Codex 路径
3. 内部使用：
   - `prepare-execution`
   - 当前 Codex 主会话实现
   - `record-execution`
4. Python 内核继续：
   - `review`
   - `repair`
   - `resume`
   - 下一 task

## Output Expectations

- summary
- changed files
- review findings
- repair decisions
- 最终状态：`DONE` 或 `BLOCKED`

## Next Steps

- 如果 review 干净，继续到下一个 task 或完成
- 如果 blocked，使用 `rf-resume`
- 如果需要独立审查，运行 `rf-spec-review`
