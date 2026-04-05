---
name: rf-spec-review
description: Use when an implementation or active change needs an independent dual-model compliance review against spec constraints, quality gates, and regression risks.
---

# RF Spec Review

## Core Philosophy

- 双模型交叉审查比单模型更容易发现盲点。
- `spec-review` 是独立工具，不依赖必须完成整个 `spec-impl`。
- 重点不是“说通过”，而是给出可操作的 Critical / Warning / Info 发现。

## Guardrails

- Review 范围严格围绕当前 OpenSpec change 和 `.railforge/` 执行工件。
- 必须同时考虑：
  - Claude 侧发现
  - Gemini 侧发现
- 不要在 review 阶段偷偷扩 scope 或直接绕过状态机修改结论。

## Severity Model

- `Critical`：必须修复
- `Warning`：应当修复
- `Info`：可选改进

## Steps

1. 运行 `railforge spec-review`
2. 收集：
   - OpenSpec constraints
   - backlog / contract
   - 最新执行结果
   - review artifacts
3. 触发 Python review gate
4. 汇总 Claude 和 Gemini 的发现
5. 按严重级别给出结论

## Next Steps

- 有 `Critical`：返回 `rf-spec-impl` 或 `rf-resume`
- 无 `Critical`：允许继续归档或下一阶段
